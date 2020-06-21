from aqt import mw
from aqt.qt import *
from .config import local_conf


_tooltipTimer = None
_tooltipLabel = None


def showToolTip(html, period=local_conf["duration"]):
    global _tooltipTimer, _tooltipLabel

    class CustomLabel(QLabel):
        def mousePressEvent(self, evt):
            evt.accept()
            self.hide()

    closeTooltip()
    aw = mw.app.activeWindow() or mw
    lab = CustomLabel(
        """\
<table cellpadding=10>
<tr>
%s
</tr>
</table>"""
        % (html),
        aw,
    )
    lab.setFrameStyle(QFrame.Panel)
    lab.setLineWidth(2)
    lab.setWindowFlags(Qt.ToolTip)
    p = QPalette()
    p.setColor(QPalette.Window, QColor(local_conf["tooltip_color"]))
    p.setColor(QPalette.WindowText, QColor("#f7f7f7"))
    lab.setPalette(p)
    vdiff = (local_conf["image_height"] - 128) / 2
    lab.move(aw.mapToGlobal(QPoint(0, -260 - vdiff + aw.height())))
    lab.show()
    _tooltipTimer = mw.progress.timer(period, closeTooltip, False)
    _tooltipLabel = lab


def closeTooltip():
    global _tooltipLabel, _tooltipTimer
    if _tooltipLabel:
        try:
            _tooltipLabel.deleteLater()
        except:
            # already deleted as parent window closed
            pass
        _tooltipLabel = None
    if _tooltipTimer:
        _tooltipTimer.stop()
        _tooltipTimer = None
