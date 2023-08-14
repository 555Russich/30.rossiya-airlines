import asyncio
import sys
from datetime import datetime
from multiprocessing import freeze_support

from PyQt5 import sip  # noqa
from PyQt5.QtCore import (
    QDate,
    QSize,
    QMetaObject,
    QCoreApplication,
    QThread,
    QObject,
    pyqtSignal
)
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLineEdit,
    QVBoxLayout,
    QDateEdit,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QPushButton,
    QTextEdit,
    QFormLayout,
)

from config import FILEPATH_DEFAULT_AUTH
from scrapper import download_reports_for_month


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(390, 342)

        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.edit_login = QLineEdit(self.centralwidget)
        self.edit_login.setObjectName(u"edit_login")


        self.edit_password = QLineEdit(self.centralwidget)
        self.edit_password.setObjectName(u"edit_password")
        self.edit_password.setEchoMode(QLineEdit.Normal)
        self.verticalLayout.addWidget(self.edit_login)
        self.verticalLayout.addWidget(self.edit_password)

        self.dateEdit = QDateEdit(self.centralwidget)
        self.dateEdit.setObjectName(u"dateEdit")
        self.dateEdit.setCalendarPopup(False)
        self.dateEdit.setDate(QDate(2000, 1, 1))

        self.verticalLayout.addWidget(self.dateEdit)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.button_collect_data = QPushButton(self.centralwidget)
        self.button_collect_data.setObjectName(u"button_collect_data")
        self.button_collect_data.setMaximumSize(QSize(399, 16777215))

        self.horizontalLayout.addWidget(self.button_collect_data)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.console = QTextEdit(self.centralwidget)
        self.console.setObjectName(u"console")
        self.console.setReadOnly(True)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.console)


        self.verticalLayout.addLayout(self.formLayout_2)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

        sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
        self.add_functions()

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Scraper rossiya-airlines", None))

        self.edit_login.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Login", None))
        self.edit_password.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Password", None))
        if FILEPATH_DEFAULT_AUTH.exists():
            login, password = FILEPATH_DEFAULT_AUTH.read_text().split('\n')
            self.edit_login.setText(login)
            self.edit_password.setText(password)
        else:
            self.edit_login.setText("")
            self.edit_password.setText("")

        now = datetime.now()
        self.dateEdit.setDate(QDate(now.year, now.month, now.day))
        self.dateEdit.setDisplayFormat(QCoreApplication.translate("MainWindow", u"M.yyyy", None))
        self.button_collect_data.setText(QCoreApplication.translate("MainWindow", u"Start", None))

    def add_functions(self) -> None:
        self.button_collect_data.clicked.connect(self.run_collect_data)

    def run_collect_data(self):
        self.console.clear()
        login, password, month = self.get_inputs()
        FILEPATH_DEFAULT_AUTH.write_text(f'{login}\n{password}')

        self.console.append('Scrapper started...')
        self.thread = QThread()
        self.worker = Worker(login=login, password=password, month=month)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.start()

        self.button_collect_data.setEnabled(False)
        self.thread.finished.connect(self.after_finished_thread)

    def get_inputs(self) -> tuple[str, str, str]:
        return self.edit_login.text(), self.edit_password.text(), '.'.join(['01', self.dateEdit.text()])

    def after_finished_thread(self):
        self.button_collect_data.setEnabled(True)
        self.console.append('Finished')

    def normalOutputWritten(self, text: str):
        self.console.append(text.rstrip())


class Worker(QObject):
    finished = pyqtSignal()

    def __init__(self, login: str, password: str, month: str):
        self.login = login
        self.password = password
        self.month = month
        super().__init__()

    def run(self):
        try:
            asyncio.run(download_reports_for_month(login=self.login, password=self.password, month=self.month))
        except Exception:
            print('ERROR occurred!')
        finally:
            self.finished.emit()


class EmittingStream(QObject):
    textWritten = pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))


if __name__ == "__main__":
    freeze_support()
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
