from aqt.qt import QDialog, QThread


sra_base_url = "https://ankiachievements.com"


class NetworkThread(QThread):
    stop_sentinel = "__stop!__"

    def __init__(self, parent, queue):
        super().__init__(parent)
        self.queue = queue
        self.was_cancelled = False

    def run(self):
        while True:
            job = self.queue.get()

            if job == self.stop_sentinel or self.was_cancelled:
                print("network thread stopped! :-)")
                break

            job()
        return

    def perform_later(self, job):
        self.queue.put(job)

    def stop_eventually(self):
        self.was_cancelled = True
        self.queue.put(self.stop_signal)


def stop_thread_on_app_close(app, thread):
    def stop():
        thread.stop_eventually()
        thread.wait()

    app.aboutToQuit.connect(stop)
