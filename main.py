import sys, datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QColor, QFont
from models import (
    get_proyectos, add_proyecto, update_proyecto, delete_proyecto,
    get_dias, add_dia, update_dia, delete_dia,
    get_tareas, add_tarea, update_tarea, delete_tarea
)
from db import ensure_database
ensure_database()
# --- helpers ---
def minutos_a_hhmm(mins):
    h = mins // 60
    m = mins % 60
    return f"{h:02}:{m:02}"

def hhmm_a_minutos(texto):
    try:
        h,m = map(int, texto.split(":"))
        return h*60+m
    except:
        return 0

# ------------------ PESTAÑAS ------------------
class ProyectosTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        add_btn = QPushButton("Añadir")
        del_btn = QPushButton("Borrar")
        btns.addWidget(add_btn)
        btns.addWidget(del_btn)
        layout.addLayout(btns)

        add_btn.clicked.connect(self.add)
        del_btn.clicked.connect(self.delete)
        self.table.itemChanged.connect(self.save_changes)

        self.setLayout(layout)
        self.load_data()

    def load_data(self):
        self.data = get_proyectos()
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.data))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID","Nombre","Orden"])
        for r,p in enumerate(self.data):
            self.table.setItem(r,0,QTableWidgetItem(str(p["id"])))
            self.table.item(r,0).setFlags(self.table.item(r,0).flags() & ~0x2)  # ID no editable
            self.table.setItem(r,1,QTableWidgetItem(p["nombre"]))
            self.table.setItem(r,2,QTableWidgetItem(str(p["orden"])))
        self.table.blockSignals(False)

    def add(self):
        add_proyecto("Nuevo Proyecto", 0)
        self.load_data()

    def delete(self):
        row = self.table.currentRow()
        if row<0: return
        p = self.data[row]
        if QMessageBox.question(self,"Borrar","¿Borrar este proyecto?")==QMessageBox.Yes:
            delete_proyecto(p["id"])
            self.load_data()

    def save_changes(self, item):
        row = item.row()
        if row<0: return
        p = self.data[row]
        id = p["id"]
        nombre = self.table.item(row,1).text()
        orden = int(self.table.item(row,2).text())
        update_proyecto(id, nombre, orden)
        self.load_data()

class DiasTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        add_btn = QPushButton("Añadir")
        del_btn = QPushButton("Borrar")
        btns.addWidget(add_btn)
        btns.addWidget(del_btn)
        layout.addLayout(btns)

        add_btn.clicked.connect(self.add)
        del_btn.clicked.connect(self.delete)
        self.table.itemChanged.connect(self.save_changes)

        self.setLayout(layout)
        self.load_data()

    def load_data(self):
        hoy = datetime.date.today()
        self.data = get_dias(hoy)
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.data))
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Fecha","Reuniones","Explotación","Máximo","Disponible","Suma Tareas","Diferencia"]
        )
        for r,d in enumerate(self.data):
            self.table.setItem(r,0,QTableWidgetItem(str(d["fecha"])))
            self.table.item(r,0).setFlags(self.table.item(r,0).flags() & ~0x2)  # fecha no editable
            self.table.setItem(r,1,QTableWidgetItem(minutos_a_hhmm(d["reuniones"])))
            self.table.setItem(r,2,QTableWidgetItem(minutos_a_hhmm(d["explotacion"])))
            self.table.setItem(r,3,QTableWidgetItem(minutos_a_hhmm(d["maximo"])))
            self.table.setItem(r,4,QTableWidgetItem(minutos_a_hhmm(d["disponible"])))
            self.table.item(r,4).setFlags(self.table.item(r,4).flags() & ~0x2)  # calculado
            self.table.setItem(r,5,QTableWidgetItem(minutos_a_hhmm(d["suma_tareas"])))
            self.table.item(r,5).setFlags(self.table.item(r,5).flags() & ~0x2)  # calculado
            diff = d["disponible"] - d["suma_tareas"]
            diff_item = QTableWidgetItem(minutos_a_hhmm(diff))
            if diff < 0:
                diff_item.setBackground(QColor(255,230,180))
            diff_item.setFlags(diff_item.flags() & ~0x2)  # calculado
            self.table.setItem(r,6,diff_item)
        self.table.blockSignals(False)

    def add(self):
        hoy = datetime.date.today()
        add_dia(hoy.strftime("%Y-%m-%d"),0,0,480)
        self.load_data()

    def delete(self):
        row = self.table.currentRow()
        if row<0: return
        d = self.data[row]
        if QMessageBox.question(self,"Borrar","¿Borrar este día?")==QMessageBox.Yes:
            delete_dia(d["fecha"])
            self.load_data()

    def save_changes(self, item):
        row = item.row()
        if row<0: return
        d = self.data[row]
        fecha = d["fecha"]
        reuniones = hhmm_a_minutos(self.table.item(row,1).text())
        explotacion = hhmm_a_minutos(self.table.item(row,2).text())
        maximo = hhmm_a_minutos(self.table.item(row,3).text())
        update_dia(fecha, reuniones, explotacion, maximo)
        self.load_data()

class PlanificacionTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        add_btn = QPushButton("Añadir")
        del_btn = QPushButton("Borrar")
        btns.addWidget(add_btn)
        btns.addWidget(del_btn)
        layout.addLayout(btns)

        add_btn.clicked.connect(self.add)
        del_btn.clicked.connect(self.delete)
        self.table.itemChanged.connect(self.save_changes)

        self.setLayout(layout)
        self.load_data()

    def load_data(self):
        hoy = datetime.date.today()
        self.data = get_tareas(hoy, order=1)
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.data))
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Proyecto","ID","Descripción","Fecha","Prioridad","Tiempo Est.","Estado"]
        )

        for r,t in enumerate(self.data):
            self.table.setItem(r,0, QTableWidgetItem(t["proyecto"]))
            self.table.item(r,0).setFlags(self.table.item(r,0).flags() & ~0x2)  # nombre proyecto no editable
            self.table.setItem(r,1, QTableWidgetItem(str(t["id"])))
            self.table.item(r,1).setFlags(self.table.item(r,1).flags() & ~0x2)  # ID no editable

            desc_item = QTableWidgetItem(t["descripcion"])
            if t["estado"]=="finalizada":
                font = desc_item.font()
                font.setStrikeOut(True)
                desc_item.setFont(font)
                desc_item.setBackground(QColor(255,200,200))
            self.table.setItem(r,2, desc_item)

            self.table.setItem(r,3, QTableWidgetItem(str(t["fecha"])))
            self.table.setItem(r,4, QTableWidgetItem(str(t["prioridad"])))
            self.table.setItem(r,5, QTableWidgetItem(minutos_a_hhmm(t["tiempo_estimado"])))
            self.table.setItem(r,6, QTableWidgetItem(t["estado"]))
        self.table.blockSignals(False)

    def add(self):
        hoy = datetime.date.today().strftime("%Y-%m-%d")
        # ⚠️ por defecto se asigna al primer proyecto
        proyectos = get_proyectos()
        if not proyectos: 
            QMessageBox.warning(self,"Error","Primero crea un proyecto")
            return
        add_tarea(proyectos[0]["id"], hoy, "Nueva tarea", 99, 60)
        self.load_data()

    def delete(self):
        row = self.table.currentRow()
        if row<0: return
        t = self.data[row]
        if QMessageBox.question(self,"Borrar","¿Borrar esta tarea?")==QMessageBox.Yes:
            delete_tarea(t["id"])
            self.load_data()

    def save_changes(self, item):
        row = item.row()
        if row<0: return
        t = self.data[row]
        id = t["id"]
        proyecto_id = t["proyecto_id"]  # no editable
        descripcion = self.table.item(row,2).text()
        fecha = self.table.item(row,3).text()
        prioridad = int(self.table.item(row,4).text())
        tiempo = hhmm_a_minutos(self.table.item(row,5).text())
        estado = self.table.item(row,6).text()
        update_tarea(id, proyecto_id, fecha, descripcion, prioridad, tiempo, estado)
        self.load_data()

# ------------------ MAIN ------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Planner de Proyectos")
        tabs = QTabWidget()
        tabs.addTab(PlanificacionTab(), "Planificación")
        tabs.addTab(DiasTab(), "Días")
        tabs.addTab(ProyectosTab(), "Proyectos")
        self.setCentralWidget(tabs)

if __name__=="__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


