from aqt.qt import QDialog, QThread
from queue import Queue
import traceback


# sra_base_url = "https://ankiachievements.com"
sra_base_url = "http://localhost:5000"
shared_headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}


stop_sentinel = "__stop!__"


def process_queue(queue):
    while True:
        job = queue.get()

        if job == stop_sentinel:
            print("network thread stopped! :-)")
            break

        try:
            job()
        except Exception as e:
            print("Exception encountered in killstreaks job thread:")
            traceback.print_exc()
        finally:
            queue.task_done()
    return


def stop_thread_on_app_close(app, queue):
    def stop():
        queue.put(stop_sentinel)

    app.aboutToQuit.connect(stop)
