"""
GUI version of CDC_test.py - send single commands to the Pico through your Transmitter class.
Put this file in the same folder as CDC_send.py, settings.py and idkfornow.py.

Flow per command (same as CDC_test.py):
    send "<cmd>\n"  ->  receive state (0 = ok, 1 = error)  ->  finish state (0 = ok, 1 = error)
"""
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk

# If the receive state is an error, the Pico may never send a "finish" reply.
# CDC_test.py always waits for it (True). Set to False to skip waiting after a receive error.
WAIT_FINISH_AFTER_RECEIVE_ERROR = False

QUICK_COMMANDS = ["CLB", "HCB", "PUP", "PDN"]


class DrawMachineGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DrawMachine - Pico command sender")
        self.geometry("680x520")

        self.transmitter = None
        self.busy = False
        self.q = queue.Queue()
        self.history, self.hist_idx = [], 0

        self._build_ui()
        self.after(50, self._poll)
        self.protocol("WM_DELETE_WINDOW", self._close)

    # ---------------- UI ----------------
    def _build_ui(self):
        top = ttk.Frame(self, padding=6)
        top.pack(fill="x")
        self.conn_btn = ttk.Button(top, text="Connect to Pico", command=self.toggle_connection)
        self.conn_btn.pack(side="left")
        self.status = ttk.Label(top, text="● disconnected", foreground="red")
        self.status.pack(side="left", padx=10)

        # quick commands
        quick = ttk.LabelFrame(self, text="Quick commands", padding=6)
        quick.pack(fill="x", padx=6)
        self.quick_btns = []
        for c in QUICK_COMMANDS:
            b = ttk.Button(quick, text=c, width=6, command=lambda c=c: self.send(c))
            b.pack(side="left", padx=2)
            self.quick_btns.append(b)

        ttk.Label(quick, text="  MOV x y (steps):").pack(side="left")
        self.mov_x = tk.StringVar(value="0")
        self.mov_y = tk.StringVar(value="0")
        ttk.Entry(quick, textvariable=self.mov_x, width=8).pack(side="left", padx=2)
        ttk.Entry(quick, textvariable=self.mov_y, width=8).pack(side="left", padx=2)
        b = ttk.Button(quick, text="MOV", width=6,
                       command=lambda: self.send(f"MOV {self.mov_x.get().strip()} {self.mov_y.get().strip()}"))
        b.pack(side="left", padx=2)
        self.quick_btns.append(b)

        ttk.Label(quick, text="  WAT s:").pack(side="left")
        self.wat = tk.StringVar(value="1")
        ttk.Entry(quick, textvariable=self.wat, width=5).pack(side="left", padx=2)
        b = ttk.Button(quick, text="WAT", width=6, command=lambda: self.send(f"WAT {self.wat.get().strip()}"))
        b.pack(side="left", padx=2)
        self.quick_btns.append(b)

        # log
        mid = ttk.Frame(self, padding=6)
        mid.pack(fill="both", expand=True)
        self.log = tk.Text(mid, state="disabled", wrap="word", bg="#111", fg="#ddd", font=("Consolas", 10))
        sb = ttk.Scrollbar(mid, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        for tag, col in [("tx", "#6cf"), ("ok", "#9f9"), ("info", "#fc6"), ("err", "#f66")]:
            self.log.tag_config(tag, foreground=col)

        # free command line
        bottom = ttk.Frame(self, padding=6)
        bottom.pack(fill="x")
        ttk.Label(bottom, text="m:").pack(side="left")
        self.cmd_var = tk.StringVar()
        self.entry = ttk.Entry(bottom, textvariable=self.cmd_var)
        self.entry.pack(side="left", fill="x", expand=True, padx=4)
        self.entry.bind("<Return>", lambda e: self.send())
        self.entry.bind("<Up>", self._hist_up)
        self.entry.bind("<Down>", self._hist_down)
        self.entry.focus()
        self.send_btn = ttk.Button(bottom, text="Send", command=self.send)
        self.send_btn.pack(side="left")
        ttk.Button(bottom, text="Clear", command=self._clear).pack(side="left", padx=(4, 0))

        self._set_controls(False)

    def _set_controls(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for b in self.quick_btns + [self.send_btn]:
            b.config(state=state)

    def _write(self, text, tag="info"):
        self.log.configure(state="normal")
        self.log.insert("end", f"[{time.strftime('%H:%M:%S')}] {text}\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    # ---------------- connection ----------------
    def toggle_connection(self):
        if self.busy:
            return
        if self.transmitter:
            self._disconnect()
        else:
            self.busy = True
            self.conn_btn.config(state="disabled")
            self.status.config(text="● connecting...", foreground="orange")
            self._write("Connecting (searching for Pico, sending SCM 0)...")
            threading.Thread(target=self._connect_worker, daemon=True).start()

    def _connect_worker(self):
        try:
            # imported here so the GUI still opens when no Pico is plugged in
            # (CDC_send searches for the Pico as soon as it is imported)
            from CDC_send import Transmitter
            tx = Transmitter(console=False)
            self.q.put(("connected", tx))
        except Exception as e:
            self.q.put(("connect_failed", f"{type(e).__name__}: {e}"))

    def _disconnect(self):
        try:
            self.transmitter.__deinit__()
        except Exception as e:
            self._write(f"Close error: {e}", "err")
        self.transmitter = None
        self.conn_btn.config(text="Connect to Pico")
        self.status.config(text="● disconnected", foreground="red")
        self._set_controls(False)
        self._write("Disconnected")

    # ---------------- sending ----------------
    def send(self, cmd=None):
        if cmd is None:
            cmd = self.cmd_var.get().strip()
            self.cmd_var.set("")
        if not cmd or self.busy or not self.transmitter:
            return
        if not self.history or self.history[-1] != cmd:
            self.history.append(cmd)
        self.hist_idx = len(self.history)

        self.busy = True
        self._set_controls(False)
        self._write(f"> {cmd}", "tx")
        threading.Thread(target=self._send_worker, args=(cmd,), daemon=True).start()

    def _send_worker(self, cmd):
        start = time.time()
        try:
            rec = self.transmitter.send_and_receive(cmd + "\n")
            self.q.put(("log", f"receive: {rec}", "ok" if rec in (0, "0") else "err"))

            fin = None
            if WAIT_FINISH_AFTER_RECEIVE_ERROR or rec in (0, "0"):
                fin = self.transmitter.send_and_receive(None)
                self.q.put(("log", f"finish:  {fin}", "ok" if fin in (0, "0") else "err"))

            self.q.put(("log", f"done in {round(time.time() - start, 5)} s", "info"))
        except Exception as e:
            self.q.put(("log", f"{type(e).__name__}: {e}", "err"))
        finally:
            self.q.put(("idle",))

    # ---------------- main-thread queue polling ----------------
    def _poll(self):
        while not self.q.empty():
            msg = self.q.get()
            kind = msg[0]
            if kind == "log":
                self._write(msg[1], msg[2])
            elif kind == "connected":
                self.transmitter = msg[1]
                self.busy = False
                self.conn_btn.config(text="Disconnect", state="normal")
                self.status.config(text="● connected", foreground="green")
                self._set_controls(True)
                self._write("Connected")
            elif kind == "connect_failed":
                self.busy = False
                self.conn_btn.config(state="normal")
                self.status.config(text="● disconnected", foreground="red")
                self._write(msg[1], "err")
            elif kind == "idle":
                self.busy = False
                if self.transmitter:
                    self._set_controls(True)
                    self.entry.focus()
        self.after(50, self._poll)

    # ---------------- history ----------------
    def _hist_up(self, _):
        if self.history and self.hist_idx > 0:
            self.hist_idx -= 1
            self.cmd_var.set(self.history[self.hist_idx])

    def _hist_down(self, _):
        if self.hist_idx < len(self.history) - 1:
            self.hist_idx += 1
            self.cmd_var.set(self.history[self.hist_idx])
        else:
            self.hist_idx = len(self.history)
            self.cmd_var.set("")

    def _close(self):
        if self.transmitter:
            try:
                self.transmitter.__deinit__()
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    DrawMachineGui().mainloop()