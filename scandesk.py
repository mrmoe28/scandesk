import json
import subprocess
import threading
import zipfile
import urllib.parse
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
from pathlib import Path

from PIL import Image
from pdf2image import convert_from_path

import customtkinter as ctk

# --- Modern Toast Notification System ---
def show_toast(parent, title, message, msg_type="info", duration=3000):
    """
    Show a modern toast/overlay notification instead of system messagebox.
    msg_type: info | success | warning | error
    """
    colors = {
        "info":    ("#0d6efd", "#0b5ed7"),
        "success": ("#198754", "#157347"),
        "warning": ("#ffc107", "#e6ac00"),
        "error":   ("#dc3545", "#b02a37"),
    }
    text_colors = {
        "info":    ("#ffffff", "#ffffff"),
        "success": ("#ffffff", "#ffffff"),
        "warning": ("#212529", "#212529"),
        "error":   ("#ffffff", "#ffffff"),
    }
    border_colors = {
        "info":    ("#4dabf7", "#4dabf7"),
        "success": ("#51cf66", "#51cf66"),
        "warning": ("#ffe066", "#ffe066"),
        "error":   ("#ff6b6b", "#ff6b6b"),
    }

    fg = colors.get(msg_type, colors["info"])
    tc = text_colors.get(msg_type, text_colors["info"])
    bc = border_colors.get(msg_type, border_colors["info"])

    overlay = ctk.CTkFrame(parent, corner_radius=18, fg_color=fg, border_width=2, border_color=bc)

    # Grid inside overlay
    overlay.grid_columnconfigure(0, weight=1)

    title_lbl = ctk.CTkLabel(
        overlay,
        text=title,
        font=ctk.CTkFont(size=15, weight="bold"),
        text_color=tc
    )
    title_lbl.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 2))

    msg_lbl = ctk.CTkLabel(
        overlay,
        text=message,
        font=ctk.CTkFont(size=13),
        text_color=tc,
        wraplength=340,
        justify="left"
    )
    msg_lbl.grid(row=1, column=0, sticky="w", padx=18, pady=(2, 14))

    # Position overlay at top-center of parent with margin
    overlay.place(relx=0.5, y=22, anchor="n")

    _after_id = None

    def dismiss():
        nonlocal _after_id
        if _after_id is not None:
            try:
                parent.after_cancel(_after_id)
            except Exception:
                pass
            _after_id = None
        try:
            overlay.destroy()
        except Exception:
            pass

    # Click anywhere on toast to dismiss early
    overlay.bind("<Button-1>", lambda e: dismiss())
    title_lbl.bind("<Button-1>", lambda e: dismiss())
    msg_lbl.bind("<Button-1>", lambda e: dismiss())

    _after_id = parent.after(duration, dismiss)


# --- Modern Confirmation Dialog ---
def show_confirm_dialog(parent, title, message, on_confirm, on_cancel=None):
    """Show a modern modal confirmation dialog using CTkToplevel."""
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.lift()
    dialog.focus_force()

    # Size and center
    w, h = 420, 200
    sw = parent.winfo_screenwidth()
    sh = parent.winfo_screenheight()
    x = int((sw - w) / 2)
    y = int((sh - h) / 2)
    dialog.geometry(f"{w}x{h}+{x}+{y}")
    dialog.resizable(False, False)

    dialog.grid_columnconfigure(0, weight=1)
    dialog.grid_rowconfigure(1, weight=1)

    # Header
    header = ctk.CTkFrame(dialog, fg_color=("#dc3545", "#b02a37"), corner_radius=0, height=48)
    header.grid(row=0, column=0, sticky="ew")
    header.grid_propagate(False)
    header.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        header,
        text=title,
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color=("#ffffff", "#ffffff")
    ).grid(row=0, column=0, sticky="w", padx=18, pady=(10, 10))

    # Body
    body = ctk.CTkFrame(dialog, fg_color="transparent")
    body.grid(row=1, column=0, sticky="nsew", padx=18, pady=14)
    body.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        body,
        text=message,
        font=ctk.CTkFont(size=13),
        wraplength=360,
        justify="left"
    ).grid(row=0, column=0, sticky="w")

    # Buttons
    btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_row.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 18))
    btn_row.grid_columnconfigure((0, 1), weight=1)

    def _confirm():
        dialog.destroy()
        if on_confirm:
            on_confirm()

    def _cancel():
        dialog.destroy()
        if on_cancel:
            on_cancel()

    ctk.CTkButton(
        btn_row,
        text="Cancel",
        command=_cancel,
        corner_radius=14,
        height=40,
        fg_color=("gray80", "gray25"),
        hover_color=("gray70", "gray32"),
        text_color=("gray10", "gray95")
    ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

    ctk.CTkButton(
        btn_row,
        text="Delete",
        command=_confirm,
        corner_radius=14,
        height=40,
        fg_color=("#dc3545", "#b02a37"),
        hover_color=("#b02a37", "#8a1c28"),
        text_color=("#ffffff", "#ffffff")
    ).grid(row=0, column=1, sticky="ew", padx=(6, 0))


DEFAULT_SCANNER_DEVICE = "airscan:e0:Canon TS3700 series (USB)"
SCAN_DIR = Path.home() / "Scans"
SCAN_DIR.mkdir(exist_ok=True)

APP_DIR = Path.home() / ".config" / "scandesk"
APP_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = APP_DIR / "settings.json"

current_session_dir = SCAN_DIR
folder_chosen_manually = False
latest_preview_file = None
preview_image_refs = []


def load_settings():
    defaults = {
        "theme": "dark",
        "default_scanner": DEFAULT_SCANNER_DEVICE,
        "default_file_type": "PDF",
        "default_resolution": "300",
        "default_scan_folder": str(SCAN_DIR),
        "email_subject": "Scanned Document",
        "email_body": "Attached is the scanned document.",
        "sidebar_width": 340
    }

    if not SETTINGS_FILE.exists():
        return defaults

    try:
        loaded = json.loads(SETTINGS_FILE.read_text())
        defaults.update(loaded)
        return defaults
    except Exception:
        return defaults


def save_settings():
    SETTINGS_FILE.write_text(json.dumps({
        "theme": theme_var.get(),
        "default_scanner": selected_scanner_id_var.get(),
        "default_file_type": file_type_var.get(),
        "default_resolution": resolution_var.get(),
        "default_scan_folder": str(SCAN_DIR),
        "email_subject": email_subject_var.get(),
        "email_body": email_body_var.get(),
        "sidebar_width": int(sidebar_width_var.get() or 310)
    }, indent=2))


def clean_folder_name(name):
    cleaned = "".join(char if char.isalnum() or char in ("-", "_", " ") else "_" for char in name.strip())
    cleaned = cleaned.replace(" ", "_")
    return cleaned or "Scan_Session"


def run_cmd(cmd, timeout=15):
    return subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout)


def run_cmd_safe(cmd, timeout=60):
    """
    Run a shell command safely, writing output to a temp file
    to avoid subprocess.PIPE deadlock on long-running operations.
    Returns a mock object with returncode, stdout, stderr.
    """
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False) as out_f:
        out_path = out_f.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.err', delete=False) as err_f:
        err_path = err_f.name

    try:
        with open(out_path, 'w') as out_fh, open(err_path, 'w') as err_fh:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=out_fh,
                stderr=err_fh
            )
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                raise

        stdout = Path(out_path).read_text()
        stderr = Path(err_path).read_text()
        from types import SimpleNamespace
        return SimpleNamespace(returncode=proc.returncode, stdout=stdout, stderr=stderr)
    finally:
        try:
            Path(out_path).unlink(missing_ok=True)
            Path(err_path).unlink(missing_ok=True)
        except Exception:
            pass

def parse_scanimage_devices(output):
    devices = []

    for line in output.splitlines():
        line = line.strip()

        if not line.startswith("device `"):
            continue

        try:
            device_id = line.split("`", 1)[1].split("'", 1)[0]
        except Exception:
            continue

        label = line
        if " is a " in line:
            label = line.split(" is a ", 1)[1].strip()

        devices.append({
            "id": device_id,
            "label": label,
            "display": f"{label} | {device_id}"
        })

    return devices


def detect_scanners():
    try:
        result = run_cmd("scanimage -L")
    except subprocess.TimeoutExpired:
        status_var.set("Scanner detection timed out.")
        return []

    if result.returncode != 0:
        status_var.set("Scanner detection failed.")
        return []

    devices = parse_scanimage_devices(result.stdout)

    if not devices:
        status_var.set("No scanners found.")
        return []

    return devices


def refresh_scanner_list():
    global scanner_devices

    scanner_devices = detect_scanners()

    if not scanner_devices:
        scanner_display_var.set("No scanners found")
        return

    displays = [device["display"] for device in scanner_devices]
    scanner_menu.configure(values=displays)

    current_device = selected_scanner_id_var.get()

    selected = None
    for device in scanner_devices:
        if device["id"] == current_device:
            selected = device
            break

    if selected is None:
        selected = scanner_devices[0]

    selected_scanner_id_var.set(selected["id"])
    scanner_display_var.set(selected["display"])
    status_var.set(f"Scanner selected: {selected['label']}")


def on_scanner_selected(display_value):
    for device in scanner_devices:
        if device["display"] == display_value:
            selected_scanner_id_var.set(device["id"])
            status_var.set(f"Scanner selected: {device['label']}")
            save_settings()
            return


def get_selected_scanner_device():
    selected = selected_scanner_id_var.get().strip()
    return selected or DEFAULT_SCANNER_DEVICE



def refresh_file_count():
    current_session_dir.mkdir(parents=True, exist_ok=True)
    files = list(current_session_dir.glob("*.pdf")) + list(current_session_dir.glob("*.png"))
    file_count_var.set(f"{len(files)} file(s) in current folder")


def set_session_folder():
    global current_session_dir, folder_chosen_manually, latest_preview_file

    folder_chosen_manually = False
    latest_preview_file = None

    folder_name = clean_folder_name(session_name_var.get())
    current_session_dir = SCAN_DIR / folder_name
    current_session_dir.mkdir(parents=True, exist_ok=True)

    session_path_var.set(str(current_session_dir))
    status_var.set(f"Session folder set: {current_session_dir.name}. Ready to scan.")
    refresh_file_count()
    refresh_preview_list()


# Prevent concurrent scans — one thread at a time
_scan_lock = threading.Lock()

def scan_document():
    global current_session_dir

    if not _scan_lock.acquire(blocking=False):
        # A scan is already in progress
        return

    try:
        if not folder_chosen_manually:
            folder_name = clean_folder_name(session_name_var.get())
            current_session_dir = SCAN_DIR / folder_name
            current_session_dir.mkdir(parents=True, exist_ok=True)
            session_path_var.set(str(current_session_dir))

        scan_button.configure(state="disabled")
        status_var.set("Scanning document...")
        progress_bar.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        progress_bar.start()
        root.update_idletasks()

        def _worker():
            try:
                scan_document_worker()
            finally:
                _scan_lock.release()

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
    except Exception:
        _scan_lock.release()
        raise


def scan_document_worker():
    file_type = file_type_var.get()
    resolution = resolution_var.get()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    session_dir = current_session_dir
    session_dir.mkdir(parents=True, exist_ok=True)

    png_path = session_dir / f"scan_{timestamp}.png"
    pdf_path = session_dir / f"scan_{timestamp}.pdf"

    scanner_device = get_selected_scanner_device()

    scan_cmd = (
        f'scanimage -d "{scanner_device}" '
        f'--format=png '
        f'--resolution {resolution} '
        f'> "{png_path}"'
    )

    try:
        result = run_cmd_safe(scan_cmd, timeout=60)
    except subprocess.TimeoutExpired:
        root.after(0, lambda: finish_scan_error("Scan Timed Out", "The scanner did not respond within 60 seconds.\nCheck that the scanner is powered on and connected."))
        return
    except Exception as error:
        root.after(0, lambda: finish_scan_error("Scan Error", str(error)))
        return

    if result.returncode != 0:
        root.after(0, lambda: finish_scan_error("Scan Failed", result.stderr or "Unknown scan error"))
        return

    if file_type == "PDF":
        root.after(0, lambda: status_var.set("Creating PDF..."))

        pdf_cmd = f'img2pdf "{png_path}" -o "{pdf_path}"'
        try:
            pdf_result = run_cmd_safe(pdf_cmd)
        except Exception as error:
            root.after(0, lambda: finish_scan_error("PDF Error", str(error)))
            return

        if pdf_result.returncode != 0:
            root.after(0, lambda: finish_scan_error("PDF Failed", pdf_result.stderr or "Could not create PDF"))
            return

        try:
            png_path.unlink()
        except Exception:
            pass

        root.after(0, lambda: finish_scan_success(pdf_path, "PDF"))
    else:
        root.after(0, lambda: finish_scan_success(png_path, "PNG"))




def build_preview_image(file_path):
    file_path = Path(file_path)

    if file_path.suffix.lower() == ".pdf":
        pages = convert_from_path(
            str(file_path),
            first_page=1,
            last_page=1,
            size=(260, 340)
        )
        image = pages[0]
    else:
        image = Image.open(file_path)

    image.thumbnail((260, 340))

    return ctk.CTkImage(
        light_image=image,
        dark_image=image,
        size=image.size
    )


def get_current_folder_scans():
    current_session_dir.mkdir(parents=True, exist_ok=True)

    files = list(current_session_dir.glob("*.pdf")) + list(current_session_dir.glob("*.png"))

    def _safe_mtime(file):
        try:
            return file.stat().st_mtime
        except (OSError, FileNotFoundError):
            return 0.0

    return sorted(files, key=_safe_mtime, reverse=True)


def load_preview(file_path=None):
    global latest_preview_file

    if file_path:
        latest_preview_file = Path(file_path)

    refresh_preview_list()



def email_single_scan(file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        show_toast(root, "File Missing", "This scan file could not be found.", "error")
        refresh_preview_list()
        refresh_file_count()
        return

    cmd = [
        "xdg-email",
        "--subject",
        f"{email_subject_var.get()} - {file_path.name}",
        "--body",
        email_body_var.get(),
        "--attach",
        str(file_path)
    ]

    try:
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=15)
    except FileNotFoundError:
        show_toast(root, "Email Failed", "xdg-email is not installed.", "error")
        return
    except subprocess.TimeoutExpired:
        show_toast(root, "Email Timed Out", "The email client did not respond within 15 seconds.", "warning")
        return
    except Exception as e:
        show_toast(root, "Email Error", str(e), "error")
        return

    if result.returncode != 0:
        show_toast(
            root,
            "Email Failed",
            result.stderr or "Could not open your default email app. Make sure Thunderbird or another email client is installed.",
            "error"
        )
        return

    status_var.set(f"Email draft opened with: {file_path.name}")


def delete_single_scan(file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        show_toast(root, "Already Deleted", "This scan file no longer exists.", "warning")
        refresh_preview_list()
        refresh_file_count()
        return

    def _do_delete():
        global latest_preview_file
        try:
            trash_cmd = subprocess.run(
                ["gio", "trash", str(file_path)],
                text=True,
                capture_output=True,
                timeout=10
            )
        except FileNotFoundError:
            trash_cmd = None
        except Exception as error:
            show_toast(root, "Delete Failed", str(error), "error")
            return

        if trash_cmd is None or trash_cmd.returncode != 0:
            try:
                file_path.unlink()
            except Exception as error:
                show_toast(root, "Delete Failed", str(error), "error")
                return

        if latest_preview_file == file_path:
            latest_preview_file = None

        status_var.set(f"Deleted: {file_path.name}")
        refresh_file_count()
        refresh_preview_list()

    show_confirm_dialog(
        root,
        "Delete Scan",
        f"Delete this scan?\n\n{file_path.name}\n\nThis will move it to Trash if available, otherwise it will delete the file.",
        on_confirm=_do_delete
    )



# Track active custom popup menu so it can be dismissed
_active_popup = None

def show_scan_menu(file_path):
    file_path = Path(file_path)
    global _active_popup

    # Dismiss any existing popup first
    if _active_popup is not None and _active_popup.winfo_exists():
        _active_popup.destroy()
        _active_popup = None

    popup = ctk.CTkFrame(root, corner_radius=16, fg_color=("gray88", "gray16"), border_width=1, border_color=("gray70", "gray32"))
    _active_popup = popup

    # Position near the mouse pointer
    px = root.winfo_pointerx() - root.winfo_rootx()
    py = root.winfo_pointery() - root.winfo_rooty()

    # Track bindings/timeouts so they can be cleaned up exactly once
    _dismissed = False
    root_bind_id = None
    esc_bind_id = None
    _timeout_id = None

    def _cleanup():
        nonlocal _dismissed
        global _active_popup
        if _dismissed:
            return
        _dismissed = True

        if _timeout_id is not None:
            try:
                root.after_cancel(_timeout_id)
            except Exception:
                pass

        if root_bind_id is not None:
            try:
                root.unbind("<Button-1>", root_bind_id)
            except Exception:
                pass

        if esc_bind_id is not None:
            try:
                root.unbind("<Escape>", esc_bind_id)
            except Exception:
                pass

        if popup.winfo_exists():
            popup.destroy()

        if _active_popup is popup:
            _active_popup = None

    # Menu items
    ctk.CTkButton(
        popup,
        text="Open",
        command=lambda: (_cleanup(), subprocess.Popen(["xdg-open", str(file_path)])),
        corner_radius=12,
        height=36,
        width=160,
        fg_color="transparent",
        hover_color=("gray80", "gray25"),
        text_color=("gray10", "gray95"),
        anchor="w"
    ).pack(fill="x", padx=8, pady=(8, 2))

    ctk.CTkButton(
        popup,
        text="Email",
        command=lambda: (_cleanup(), email_single_scan(file_path)),
        corner_radius=12,
        height=36,
        width=160,
        fg_color="transparent",
        hover_color=("gray80", "gray25"),
        text_color=("gray10", "gray95"),
        anchor="w"
    ).pack(fill="x", padx=8, pady=2)

    separator = ctk.CTkFrame(popup, height=1, fg_color=("gray70", "gray32"))
    separator.pack(fill="x", padx=12, pady=4)

    ctk.CTkButton(
        popup,
        text="Delete",
        command=lambda: (_cleanup(), delete_single_scan(file_path)),
        corner_radius=12,
        height=36,
        width=160,
        fg_color="transparent",
        hover_color=("#ff6b6b", "#8a1c28"),
        text_color=("#dc3545", "#ff6b6b"),
        anchor="w"
    ).pack(fill="x", padx=8, pady=(2, 8))

    # Wait for popup to compute size, then clamp to window bounds
    popup.update_idletasks()
    pw = popup.winfo_reqwidth()
    ph = popup.winfo_reqheight()

    rw = root.winfo_width()
    rh = root.winfo_height()

    x = min(px, rw - pw - 12)
    y = min(py, rh - ph - 12)
    x = max(8, x)
    y = max(8, y)

    popup.place(x=x, y=y)

    # Dismiss when clicking anywhere else on the app
    def _on_click_outside(event):
        if not popup.winfo_exists():
            return
        # Check if click is inside popup
        try:
            wx = popup.winfo_x()
            wy = popup.winfo_y()
            ww = popup.winfo_width()
            wh = popup.winfo_height()
            if wx <= event.x <= wx + ww and wy <= event.y <= wy + wh:
                return  # click inside popup, ignore
        except Exception:
            pass
        _cleanup()

    root_bind_id = root.bind("<Button-1>", _on_click_outside, add="+")

    # Also dismiss on Escape
    def _on_escape(event):
        _cleanup()

    esc_bind_id = root.bind("<Escape>", _on_escape, add="+")

    # Auto-dismiss after 8 seconds
    def _timeout_dismiss():
        _cleanup()

    _timeout_id = root.after(8000, _timeout_dismiss)


def refresh_preview_list():
    global latest_preview_file

    preview_image_refs.clear()

    for child in preview_list_frame.winfo_children():
        child.destroy()

    files = get_current_folder_scans()

    if not files:
        empty_label = ctk.CTkLabel(
            preview_list_frame,
            text="No scans yet.",
            height=120,
            text_color=("gray35", "gray70")
        )
        empty_label.pack(fill="x", padx=8, pady=8)

        preview_filename_var.set("No scans in folder")
        preview_breadcrumb_var.set("Scans")
        latest_preview_file = None
        return

    if latest_preview_file is None or latest_preview_file not in files:
        latest_preview_file = files[0]

    preview_filename_var.set(f"{len(files)} scan(s)")
    preview_breadcrumb_var.set(f"Scans > {current_session_dir.name}")

    total = len(files)

    for index, file in enumerate(files):
        scan_number = total - index
        is_latest = index == 0

        item = ctk.CTkFrame(preview_list_frame, corner_radius=16)
        item.pack(fill="x", padx=8, pady=8)

        title_text = f"Scan {scan_number}"
        if is_latest:
            title_text = f"Latest • Scan {scan_number}"

        title_row = ctk.CTkFrame(item, fg_color="transparent")
        title_row.pack(fill="x", padx=10, pady=(10, 4))
        title_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            title_row,
            text=title_text,
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        menu_button = ctk.CTkButton(
            title_row,
            text="☰",
            command=lambda selected_file=file: show_scan_menu(selected_file),
            corner_radius=14,
            width=34,
            height=30,
            fg_color=("gray80", "gray25"),
            hover_color=("gray70", "gray32"),
            text_color=("gray10", "gray95")
        )
        menu_button.grid(row=0, column=1, sticky="e")

        try:
            file_path = Path(file)

            if file_path.suffix.lower() == ".pdf":
                pages = convert_from_path(
                    str(file_path),
                    first_page=1,
                    last_page=1,
                    size=(220, 285)
                )
                image = pages[0]
            else:
                image = Image.open(file_path)

            image.thumbnail((220, 285))

            ctk_image = ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=image.size
            )
            preview_image_refs.append(ctk_image)

            image_label = ctk.CTkLabel(
                item,
                image=ctk_image,
                text="",
                width=230,
                height=300,
                corner_radius=14,
                fg_color=("gray88", "gray16")
            )
            image_label.pack(anchor="center", padx=10, pady=(0, 8))
        except Exception:
            ctk.CTkLabel(
                item,
                text="Preview unavailable",
                width=240,
                height=120,
                corner_radius=14,
                fg_color=("gray88", "gray16")
            ).pack(anchor="center", padx=10, pady=(0, 8))

        ctk.CTkLabel(
            item,
            text=file.name,
            text_color=("gray35", "gray70"),
            wraplength=220,
            justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 6))

    # Force redraw so CTkScrollableFrame shows new images immediately
    preview_list_frame.update()



def open_preview_file():
    if not latest_preview_file:
        show_toast(root, "No Preview", "No scanned document is available to preview yet.", "warning")
        return

    subprocess.Popen(["xdg-open", str(latest_preview_file)])


def close_preview():
    global latest_preview_file

    latest_preview_file = None

    for child in preview_list_frame.winfo_children():
        child.destroy()

    empty_label = ctk.CTkLabel(
        preview_list_frame,
        text="Preview closed. Your saved scans were not deleted.",
        height=120,
        text_color=("gray35", "gray70")
    )
    empty_label.pack(fill="x", padx=10, pady=10)

    preview_filename_var.set("Preview closed.")
    preview_breadcrumb_var.set("Scans")
    status_var.set("Preview closed. Your saved scans were not deleted.")


def finish_scan_success(file_path, file_type):
    try:
        progress_bar.stop()
        progress_bar.grid_remove()
        scan_button.configure(state="normal")
        status_var.set(f"Saved {file_type}: {file_path.name}")
        refresh_file_count()
        load_preview(file_path)
    except Exception as error:
        progress_bar.stop()
        progress_bar.grid_remove()
        scan_button.configure(state="normal")
        status_var.set("Scan finished but preview failed")
        show_toast(root, "Preview Error", f"Scan saved, but preview failed:\n{error}", "warning")


def finish_scan_error(title, message):
    try:
        progress_bar.stop()
        progress_bar.grid_remove()
        scan_button.configure(state="normal")
        status_var.set("Scan failed")
        show_toast(root, title, message, "error")
    except Exception:
        # Nuclear fallback — if even the toast fails, at least unstick the UI
        try:
            progress_bar.stop()
            progress_bar.grid_remove()
            scan_button.configure(state="normal")
        except Exception:
            pass


def open_scan_folder():
    global current_session_dir, latest_preview_file, folder_chosen_manually

    selected_folder = ""

    try:
        zenity_result = subprocess.run(
            [
                "zenity",
                "--file-selection",
                "--directory",
                "--title=Choose Scan Folder",
                f"--filename={str(SCAN_DIR)}/"
            ],
            text=True,
            capture_output=True,
            timeout=30
        )
        if zenity_result.returncode == 0:
            selected_folder = zenity_result.stdout.strip()
    except (FileNotFoundError, subprocess.SubprocessError):
        pass

    if not selected_folder:
        selected_folder = filedialog.askdirectory(
            title="Choose Scan Folder",
            initialdir=str(SCAN_DIR)
        )

    if not selected_folder:
        status_var.set("Folder selection cancelled.")
        return

    folder_chosen_manually = True
    current_session_dir = Path(selected_folder)
    current_session_dir.mkdir(parents=True, exist_ok=True)

    latest_preview_file = None
    session_name_var.set(current_session_dir.name)
    session_path_var.set(str(current_session_dir))

    refresh_file_count()
    refresh_preview_list()

    status_var.set(f"Loaded folder and set as scan destination: {current_session_dir}")

def get_latest_scan():
    files = list(current_session_dir.glob("*.pdf")) + list(current_session_dir.glob("*.png"))
    if not files:
        return None
    def _safe_mtime(file):
        try:
            return file.stat().st_mtime
        except (OSError, FileNotFoundError):
            return 0.0
    return max(files, key=_safe_mtime)


def email_latest_scan():
    latest_file = get_latest_scan()

    if not latest_file:
        show_toast(root, "No Scans Found", "No PDF or PNG scans were found in the current session folder.", "warning")
        return

    cmd = [
        "xdg-email",
        "--subject",
        email_subject_var.get(),
        "--body",
        email_body_var.get(),
        "--attach",
        str(latest_file)
    ]

    try:
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=15)
    except FileNotFoundError:
        show_toast(root, "Email Failed", "xdg-email is not installed.", "error")
        return
    except subprocess.TimeoutExpired:
        show_toast(root, "Email Timed Out", "The email client did not respond within 15 seconds.", "warning")
        return
    except Exception as e:
        show_toast(root, "Email Error", str(e), "error")
        return

    if result.returncode != 0:
        show_toast(
            root,
            "Email Failed",
            result.stderr or "Could not open your default email app. Make sure Thunderbird or another email client is installed.",
            "error"
        )
        return

    status_var.set(f"Email draft opened with: {latest_file.name}")





def email_current_folder_zip():
    current_session_dir.mkdir(parents=True, exist_ok=True)

    def _safe_mtime(file):
        try:
            return file.stat().st_mtime
        except (OSError, FileNotFoundError):
            return 0.0

    files = sorted(
        list(current_session_dir.glob("*.pdf")) +
        list(current_session_dir.glob("*.png")) +
        list(current_session_dir.glob("*.jpg")) +
        list(current_session_dir.glob("*.jpeg")),
        key=_safe_mtime
    )

    files = [file for file in files if "_email_exports" not in str(file)]

    if not files:
        show_toast(root, "No Scans Found", "No scan files were found in the current session folder.", "warning")
        return

    subject = f"{email_subject_var.get()} - {current_session_dir.name}"
    body = (
        f"{email_body_var.get()}\n\n"
        "The scan folder has been opened. Drag the PDF files from the folder into this Gmail draft."
    )

    gmail_url = (
        "https://mail.google.com/mail/?view=cm&fs=1"
        f"&su={urllib.parse.quote(subject)}"
        f"&body={urllib.parse.quote(body)}"
    )

    try:
        subprocess.Popen(["xdg-open", gmail_url])
        subprocess.Popen(["xdg-open", str(current_session_dir)])
    except Exception as error:
        show_toast(root, "Open Gmail Failed", str(error), "error")
        status_var.set("Could not open Gmail compose.")
        return

    show_toast(
        root,
        "Gmail Compose Opened",
        (
            f"Gmail compose was opened.\n\n"
            f"The scan folder was also opened here:\n{current_session_dir}\n\n"
            "Drag the PDF files directly into the Gmail draft, then send."
        ),
        "success",
        duration=5000
    )

    status_var.set(f"Opened Gmail compose and folder with {len(files)} scan file(s).")


def email_current_folder():
    current_session_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(
        list(current_session_dir.glob("*.pdf")) + list(current_session_dir.glob("*.png")),
        key=lambda file: file.stat().st_mtime
    )

    if not files:
        show_toast(root, "No Scans Found", "No PDF or PNG scans were found in the current session folder.", "warning")
        return

    cmd = [
        "xdg-email",
        "--subject",
        f"Scanned Documents - {current_session_dir.name}",
        "--body",
        email_body_var.get()
    ]

    for file in files:
        cmd.extend(["--attach", str(file)])

    result = subprocess.run(cmd, text=True, capture_output=True, timeout=15)

    if result.returncode != 0:
        show_toast(
            root,
            "Email Failed",
            result.stderr or "Could not open your default email app. Make sure Thunderbird or another email client is installed.",
            "error"
        )
        return

    status_var.set(f"Email draft opened with {len(files)} file(s).")


def test_scanner():
    result = run_cmd("scanimage -L")
    show_toast(root, "Detected Scanners", result.stdout or result.stderr or "No scanner detected", "info", duration=5000)


def search_for_new_scanners():
    refresh_scanner_list()


def toggle_theme():
    if theme_var.get() == "dark":
        theme_var.set("light")
        ctk.set_appearance_mode("light")
        theme_button.configure(text="Dark Mode")
    else:
        theme_var.set("dark")
        ctk.set_appearance_mode("dark")
        theme_button.configure(text="Light Mode")

    save_settings()



def enable_mouse_scroll(widget):
    def _on_mousewheel(event):
        try:
            widget._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def _on_linux_scroll_up(event):
        try:
            widget._parent_canvas.yview_scroll(-1, "units")
        except Exception:
            pass

    def _on_linux_scroll_down(event):
        try:
            widget._parent_canvas.yview_scroll(1, "units")
        except Exception:
            pass

    widget.bind_all("<MouseWheel>", _on_mousewheel)
    widget.bind_all("<Button-4>", _on_linux_scroll_up)
    widget.bind_all("<Button-5>", _on_linux_scroll_down)



# Prevent multiple settings windows
_settings_window_ref = None

def open_settings_window():
    global _settings_window_ref
    if _settings_window_ref is not None and _settings_window_ref.winfo_exists():
        _settings_window_ref.lift()
        _settings_window_ref.focus_force()
        return

    settings_window = ctk.CTkToplevel(root)
    _settings_window_ref = settings_window
    settings_window.title("Settings")
    settings_width = int(root.winfo_screenwidth() * 0.72)
    settings_height = int(root.winfo_screenheight() * 0.82)
    settings_x = int((root.winfo_screenwidth() - settings_width) / 2)
    settings_y = int((root.winfo_screenheight() - settings_height) / 2)

    settings_window.geometry(f"{settings_width}x{settings_height}+{settings_x}+{settings_y}")
    settings_window.minsize(680, 620)
    settings_window.resizable(True, True)
    settings_window.transient(root)
    settings_window.lift()
    settings_window.focus_force()
    settings_window.grab_set()

    def _on_settings_close():
        global _settings_window_ref
        _settings_window_ref = None
        settings_window.destroy()

    settings_window.protocol("WM_DELETE_WINDOW", _on_settings_close)

    wrapper = ctk.CTkScrollableFrame(settings_window, corner_radius=0)
    wrapper.pack(fill="both", expand=True, padx=18, pady=18)
    wrapper.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        wrapper,
        text="Settings",
        font=ctk.CTkFont(size=26, weight="bold")
    ).grid(row=0, column=0, sticky="w", pady=(0, 16))

    scanner_card = ctk.CTkFrame(wrapper, corner_radius=20)
    scanner_card.grid(row=1, column=0, sticky="ew", pady=10)
    scanner_card.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        scanner_card,
        text="Scanner",
        font=ctk.CTkFont(size=17, weight="bold")
    ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))

    ctk.CTkLabel(
        scanner_card,
        textvariable=selected_scanner_id_var,
        text_color=("gray35", "gray70"),
        wraplength=520
    ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 8))

    ctk.CTkButton(
        scanner_card,
        text="Search for Scanners",
        command=search_for_new_scanners,
        corner_radius=18,
        height=40
    ).grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))

    scan_card_settings = ctk.CTkFrame(wrapper, corner_radius=20)
    scan_card_settings.grid(row=2, column=0, sticky="ew", pady=10)
    scan_card_settings.grid_columnconfigure((0, 1), weight=1)

    ctk.CTkLabel(
        scan_card_settings,
        text="Scan Defaults",
        font=ctk.CTkFont(size=17, weight="bold")
    ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 8))

    ctk.CTkLabel(scan_card_settings, text="Default file type").grid(row=1, column=0, sticky="w", padx=16)
    ctk.CTkLabel(scan_card_settings, text="Default resolution").grid(row=1, column=1, sticky="w", padx=16)

    settings_file_type = ctk.CTkOptionMenu(
        scan_card_settings,
        variable=file_type_var,
        values=["PDF", "PNG"],
        corner_radius=18,
        height=40
    )
    settings_file_type.grid(row=2, column=0, sticky="ew", padx=16, pady=(6, 16))

    settings_resolution = ctk.CTkOptionMenu(
        scan_card_settings,
        variable=resolution_var,
        values=["150", "300", "600"],
        corner_radius=18,
        height=40
    )
    settings_resolution.grid(row=2, column=1, sticky="ew", padx=16, pady=(6, 16))

    email_settings_card = ctk.CTkFrame(wrapper, corner_radius=20)
    email_settings_card.grid(row=3, column=0, sticky="ew", pady=10)
    email_settings_card.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        email_settings_card,
        text="Email Defaults",
        font=ctk.CTkFont(size=17, weight="bold")
    ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))

    ctk.CTkLabel(email_settings_card, text="Subject").grid(row=1, column=0, sticky="w", padx=16)
    ctk.CTkEntry(
        email_settings_card,
        textvariable=email_subject_var,
        corner_radius=14,
        height=40
    ).grid(row=2, column=0, sticky="ew", padx=16, pady=(6, 12))

    ctk.CTkLabel(email_settings_card, text="Body").grid(row=3, column=0, sticky="w", padx=16)
    ctk.CTkEntry(
        email_settings_card,
        textvariable=email_body_var,
        corner_radius=14,
        height=40
    ).grid(row=4, column=0, sticky="ew", padx=16, pady=(6, 16))

    appearance_card = ctk.CTkFrame(wrapper, corner_radius=20)
    appearance_card.grid(row=4, column=0, sticky="ew", pady=10)
    appearance_card.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        appearance_card,
        text="Appearance",
        font=ctk.CTkFont(size=17, weight="bold")
    ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))

    ctk.CTkButton(
        appearance_card,
        text="Toggle Light / Dark Mode",
        command=toggle_theme,
        corner_radius=18,
        height=40
    ).grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))

    ctk.CTkLabel(appearance_card, text="Sidebar width").grid(row=2, column=0, sticky="w", padx=16)

    ctk.CTkEntry(
        appearance_card,
        textvariable=sidebar_width_var,
        corner_radius=14,
        height=40
    ).grid(row=3, column=0, sticky="ew", padx=16, pady=(6, 16))

    def save_and_close():
        save_settings()
        try:
            sidebar.configure(width=int(sidebar_width_var.get() or 310))
        except Exception:
            pass
        status_var.set("Settings saved.")
        settings_window.destroy()

    ctk.CTkButton(
        wrapper,
        text="Save Settings",
        command=save_and_close,
        corner_radius=22,
        height=48,
        font=ctk.CTkFont(size=15, weight="bold")
    ).grid(row=5, column=0, sticky="ew", pady=(18, 8))

    ctk.CTkButton(
        wrapper,
        text="Close",
        command=settings_window.destroy,
        corner_radius=22,
        height=44,
        fg_color=("gray80", "gray25"),
        hover_color=("gray70", "gray32"),
        text_color=("gray10", "gray95")
    ).grid(row=6, column=0, sticky="ew", pady=(0, 12))


settings = load_settings()

ctk.set_appearance_mode(settings.get("theme", "dark"))
ctk.set_default_color_theme("blue")


def set_scandesk_window_icon(window):
    """Set ScanDesk app/window icon."""
    try:
        icon_path = Path(__file__).resolve().parent / "assets" / "scandesk.png"
        if icon_path.exists():
            icon_img = tk.PhotoImage(file=str(icon_path))
            window.iconphoto(True, icon_img)
            window._scandesk_icon_img = icon_img
        else:
            print(f"Icon not found: {icon_path}")
    except Exception as e:
        print(f"Icon load warning: {e}")

root = ctk.CTk()
set_scandesk_window_icon(root)
root.title("ScanDesk")

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

scale = 0.9 if screen_height <= 768 else 1.0
ctk.set_widget_scaling(scale)
ctk.set_window_scaling(scale)

window_width = min(1180, int(screen_width * 0.92))
window_height = min(840, int(screen_height * 0.88))
window_x = int((screen_width - window_width) / 2)
window_y = int((screen_height - window_height) / 2)

root.geometry(f"{window_width}x{window_height}+{window_x}+{window_y}")
root.minsize(1040, 700)
root.resizable(True, True)

theme_var = tk.StringVar(value=settings.get("theme", "dark"))
scanner_devices = []
selected_scanner_id_var = tk.StringVar(value=settings.get("default_scanner", DEFAULT_SCANNER_DEVICE))
scanner_display_var = tk.StringVar(value=settings.get("default_scanner", DEFAULT_SCANNER_DEVICE))
session_name_var = tk.StringVar(value=datetime.now().strftime("Scan_Session_%Y-%m-%d"))
session_path_var = tk.StringVar(value=str(SCAN_DIR))
file_count_var = tk.StringVar(value="0 file(s) in current folder")
file_type_var = tk.StringVar(value=settings.get("default_file_type", "PDF"))
resolution_var = tk.StringVar(value=settings.get("default_resolution", "300"))
email_subject_var = tk.StringVar(value=settings.get("email_subject", "Scanned Document"))
email_body_var = tk.StringVar(value=settings.get("email_body", "Attached is the scanned document."))
sidebar_width_var = tk.StringVar(value=str(settings.get("sidebar_width", 340)))
status_var = tk.StringVar(value="Ready. Set a session folder, then scan each page.")
preview_filename_var = tk.StringVar(value="No document scanned yet.")
preview_breadcrumb_var = tk.StringVar(value="Scans")

app = ctk.CTkFrame(root, corner_radius=0)
app.pack(fill="both", expand=True, padx=18, pady=18)
app.grid_columnconfigure(0, weight=0, minsize=int(settings.get("sidebar_width", 340)))
app.grid_columnconfigure(1, weight=1, minsize=640)
app.grid_rowconfigure(0, weight=1)

sidebar = ctk.CTkFrame(app, corner_radius=22, width=int(settings.get("sidebar_width", 340)))
sidebar.grid(row=0, column=0, sticky="nsw", padx=(0, 14))
sidebar.grid_propagate(False)
sidebar.grid_rowconfigure(3, weight=1)
sidebar.grid_columnconfigure(0, weight=1)

sidebar_header = ctk.CTkFrame(sidebar, fg_color="transparent")
sidebar_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(18, 8))
sidebar_header.grid_columnconfigure(0, weight=1)

ctk.CTkLabel(
    sidebar_header,
    text="Scans",
    font=ctk.CTkFont(size=22, weight="bold")
).grid(row=0, column=0, sticky="w")

refresh_preview_button = ctk.CTkButton(
    sidebar_header,
    text="Refresh",
    command=refresh_preview_list,
    corner_radius=18,
    height=34,
    width=86,
    fg_color=("gray80", "gray25"),
    hover_color=("gray70", "gray32"),
    text_color=("gray10", "gray95")
)
refresh_preview_button.grid(row=0, column=1, sticky="e")

breadcrumb_label = ctk.CTkLabel(
    sidebar,
    textvariable=preview_breadcrumb_var,
    text_color=("#1f6aa5", "#64b5f6"),
    anchor="w",
    wraplength=270
)
breadcrumb_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))

ctk.CTkLabel(
    sidebar,
    textvariable=preview_filename_var,
    text_color=("gray35", "gray70"),
    anchor="w",
    wraplength=270
).grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 8))

preview_list_frame = ctk.CTkScrollableFrame(
    sidebar,
    corner_radius=18,
    fg_color=("gray90", "gray14")
)
preview_list_frame.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 12))

close_preview_button = ctk.CTkButton(
    sidebar,
    text="Clear Preview",
    command=close_preview,
    corner_radius=18,
    height=40,
    fg_color=("gray80", "gray25"),
    hover_color=("gray70", "gray32"),
    text_color=("gray10", "gray95")
)
close_preview_button.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 16))

main_scroll = ctk.CTkScrollableFrame(app, corner_radius=22)
main_scroll.grid(row=0, column=1, sticky="nsew")
main_scroll.grid_columnconfigure(0, weight=1)

main = ctk.CTkFrame(main_scroll, corner_radius=22)
main.pack(fill="both", expand=True, padx=0, pady=0)
main.grid_columnconfigure(0, weight=1)

# --- Header with icon and title ---
header = ctk.CTkFrame(main, fg_color="transparent")
header.grid(row=0, column=0, sticky="ew", padx=22, pady=(22, 12))
header.grid_columnconfigure(0, weight=1)
header.grid_columnconfigure(1, weight=0)

header_left = ctk.CTkFrame(header, fg_color="transparent")
header_left.grid(row=0, column=0, sticky="w")
header_left.grid_columnconfigure(1, weight=1)

# Load and resize header icon using CTkImage (matches preview image pattern)
try:
    icon_path = Path(__file__).resolve().parent / "assets" / "scandesk.png"
    _header_icon_pil = Image.open(str(icon_path)).convert("RGBA")
    _resample = getattr(Image, "Resampling", Image).LANCZOS  # type: ignore[attr-defined]
    _header_icon_pil = _header_icon_pil.resize((56, 56), _resample)
    header_icon_photo = ctk.CTkImage(
        light_image=_header_icon_pil,
        dark_image=_header_icon_pil,
        size=(56, 56)
    )
    header_icon_label = ctk.CTkLabel(header_left, image=header_icon_photo, text="")
    header_icon_label._keep_ref = header_icon_photo  # type: ignore[attr-defined]  # persist reference
    header_icon_label.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 14))
except Exception:
    header_icon_photo = None

header_text_frame = ctk.CTkFrame(header_left, fg_color="transparent")
header_text_frame.grid(row=0, column=1, sticky="w")

title = ctk.CTkLabel(
    header_text_frame,
    text="ScanDesk",
    font=ctk.CTkFont(size=28, weight="bold")
)
title.grid(row=0, column=0, sticky="w")

subtitle = ctk.CTkLabel(
    header_text_frame,
    text="Scan, organize, and email documents from your Linux desktop.",
    font=ctk.CTkFont(size=13),
    text_color=("gray35", "gray70")
)
subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

header_buttons = ctk.CTkFrame(header, fg_color="transparent")
header_buttons.grid(row=0, column=1, rowspan=2, sticky="e", padx=(16, 0))

settings_button = ctk.CTkButton(
    header_buttons,
    text="Settings",
    command=open_settings_window,
    corner_radius=18,
    height=36,
    width=110,
    fg_color=("gray80", "gray25"),
    hover_color=("gray70", "gray32"),
    text_color=("gray10", "gray95")
)
settings_button.grid(row=0, column=0, padx=(0, 8))

theme_button = ctk.CTkButton(
    header_buttons,
    text="Light Mode" if theme_var.get() == "dark" else "Dark Mode",
    command=toggle_theme,
    corner_radius=18,
    height=36,
    width=120
)
theme_button.grid(row=0, column=1)

scanner_card = ctk.CTkFrame(main, corner_radius=22)
scanner_card.grid(row=1, column=0, sticky="ew", padx=22, pady=12)
scanner_card.grid_columnconfigure(0, weight=1)

ctk.CTkLabel(
    scanner_card,
    text="Scanner Device",
    font=ctk.CTkFont(size=17, weight="bold")
).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 8))

ctk.CTkLabel(
    scanner_card,
    text="Choose which connected scanner to use.",
    text_color=("gray35", "gray70")
).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 8))

scanner_menu = ctk.CTkOptionMenu(
    scanner_card,
    variable=scanner_display_var,
    values=[DEFAULT_SCANNER_DEVICE],
    command=on_scanner_selected,
    corner_radius=18,
    height=42
)
scanner_menu.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 12))

scanner_buttons = ctk.CTkFrame(scanner_card, fg_color="transparent")
scanner_buttons.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 18))
scanner_buttons.grid_columnconfigure((0, 1), weight=1)

search_scanners_button = ctk.CTkButton(
    scanner_buttons,
    text="Search for Scanners",
    command=search_for_new_scanners,
    corner_radius=18,
    height=42
)
search_scanners_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

test_button_top = ctk.CTkButton(
    scanner_buttons,
    text="Show Raw Detection",
    command=test_scanner,
    corner_radius=18,
    height=42,
    fg_color=("gray80", "gray25"),
    hover_color=("gray70", "gray32"),
    text_color=("gray10", "gray95")
)
test_button_top.grid(row=0, column=1, sticky="ew", padx=(8, 0))

session_card = ctk.CTkFrame(main, corner_radius=22)
session_card.grid(row=2, column=0, sticky="ew", padx=22, pady=12)
session_card.grid_columnconfigure(0, weight=1)

ctk.CTkLabel(
    session_card,
    text="Scan Session",
    font=ctk.CTkFont(size=17, weight="bold")
).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 8))

ctk.CTkLabel(
    session_card,
    text="Folder name",
    text_color=("gray35", "gray70")
).grid(row=1, column=0, sticky="w", padx=18)

session_entry = ctk.CTkEntry(
    session_card,
    textvariable=session_name_var,
    corner_radius=14,
    height=42
)
session_entry.grid(row=2, column=0, sticky="ew", padx=18, pady=(6, 12))

session_buttons = ctk.CTkFrame(session_card, fg_color="transparent")
session_buttons.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 12))
session_buttons.grid_columnconfigure((0, 1), weight=1)

set_folder_button = ctk.CTkButton(
    session_buttons,
    text="Set Session Folder",
    command=set_session_folder,
    corner_radius=18,
    height=42
)
set_folder_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

open_folder_button = ctk.CTkButton(
    session_buttons,
    text="Choose Folder",
    command=open_scan_folder,
    corner_radius=18,
    height=42,
    fg_color=("gray80", "gray25"),
    hover_color=("gray70", "gray32"),
    text_color=("gray10", "gray95")
)
open_folder_button.grid(row=0, column=1, sticky="ew", padx=(8, 0))

ctk.CTkLabel(
    session_card,
    textvariable=session_path_var,
    text_color=("gray35", "gray70"),
    wraplength=620
).grid(row=4, column=0, sticky="w", padx=18, pady=(0, 4))

ctk.CTkLabel(
    session_card,
    textvariable=file_count_var,
    text_color=("#1f6aa5", "#64b5f6")
).grid(row=5, column=0, sticky="w", padx=18, pady=(0, 18))

settings_card = ctk.CTkFrame(main, corner_radius=22)
settings_card.grid(row=3, column=0, sticky="ew", padx=22, pady=12)
settings_card.grid_columnconfigure((0, 1), weight=1)

ctk.CTkLabel(
    settings_card,
    text="Scan Settings",
    font=ctk.CTkFont(size=17, weight="bold")
).grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(18, 10))

ctk.CTkLabel(settings_card, text="File type", text_color=("gray35", "gray70")).grid(row=1, column=0, sticky="w", padx=18)
ctk.CTkLabel(settings_card, text="Resolution", text_color=("gray35", "gray70")).grid(row=1, column=1, sticky="w", padx=18)

file_type_menu = ctk.CTkOptionMenu(
    settings_card,
    variable=file_type_var,
    values=["PDF", "PNG"],
    corner_radius=18,
    height=42
)
file_type_menu.grid(row=2, column=0, sticky="ew", padx=18, pady=(6, 18))

resolution_menu = ctk.CTkOptionMenu(
    settings_card,
    variable=resolution_var,
    values=["150", "300", "600"],
    corner_radius=18,
    height=42
)
resolution_menu.grid(row=2, column=1, sticky="ew", padx=18, pady=(6, 18))

scan_card = ctk.CTkFrame(main, fg_color="transparent")
scan_card.grid(row=4, column=0, sticky="ew", padx=22, pady=12)
scan_card.grid_columnconfigure(0, weight=1)

scan_button = ctk.CTkButton(
    scan_card,
    text="Scan Document",
    command=scan_document,
    corner_radius=24,
    height=54,
    font=ctk.CTkFont(size=16, weight="bold"),
    fg_color=("#198754", "#2fa866"),
    hover_color=("#157347", "#238a52")
)
scan_button.grid(row=0, column=0, sticky="ew")

progress_bar = ctk.CTkProgressBar(scan_card, mode="indeterminate", corner_radius=12, height=12)
progress_bar.grid(row=1, column=0, sticky="ew", pady=(12, 0))
progress_bar.grid_remove()

email_card = ctk.CTkFrame(main, corner_radius=22)
email_card.grid(row=5, column=0, sticky="ew", padx=22, pady=12)
email_card.grid_columnconfigure((0, 1), weight=1)

ctk.CTkLabel(
    email_card,
    text="Email",
    font=ctk.CTkFont(size=17, weight="bold")
).grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(18, 10))

email_latest_button = ctk.CTkButton(
    email_card,
    text="Email Latest Scan",
    command=email_latest_scan,
    corner_radius=18,
    height=44,
    fg_color=("gray80", "gray25"),
    hover_color=("gray70", "gray32"),
    text_color=("gray10", "gray95")
)
email_latest_button.grid(row=1, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 12))

email_zip_button = ctk.CTkButton(
    email_card,
    text="Open Gmail + PDF Folder",
    command=email_current_folder_zip,
    corner_radius=18,
    height=44,
    fg_color=("#6f42c1", "#5a32a3"),
    hover_color=("#5a32a3", "#432874")
)
email_zip_button.grid(row=2, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 18))

tools_card = ctk.CTkFrame(main, fg_color="transparent")
tools_card.grid(row=6, column=0, sticky="ew", padx=22, pady=12)
tools_card.grid_columnconfigure(0, weight=1)

test_button = ctk.CTkButton(
    tools_card,
    text="Refresh Scanner List",
    command=search_for_new_scanners,
    corner_radius=18,
    height=42,
    fg_color=("gray80", "gray25"),
    hover_color=("gray70", "gray32"),
    text_color=("gray10", "gray95")
)
test_button.grid(row=0, column=0, sticky="ew")

status_bar = ctk.CTkLabel(
    main,
    textvariable=status_var,
    corner_radius=18,
    height=42,
    fg_color=("gray85", "gray18"),
    text_color=("gray15", "gray85"),
    anchor="w"
)
status_bar.grid(row=7, column=0, sticky="ew", padx=22, pady=(12, 22))


def clamp_sidebar_width():
    try:
        width = int(sidebar_width_var.get() or 340)
    except Exception:
        width = 340

    width = max(300, min(width, 420))
    sidebar_width_var.set(str(width))
    sidebar.configure(width=width)
    app.grid_columnconfigure(0, minsize=width)


def on_root_resize(event):
    if event.widget != root:
        return

    clamp_sidebar_width()


root.bind("<Configure>", on_root_resize)

refresh_file_count()
# Defer heavy startup work so the window appears instantly
root.after(100, refresh_preview_list)
root.after(150, refresh_scanner_list)

root.mainloop()
