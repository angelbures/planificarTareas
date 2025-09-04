import sys, datetime
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox, QDateEdit, QComboBox
)
from PyQt5.QtGui import QColor, QFont
from models import (
    get_proyectos, add_proyecto, update_proyecto, delete_proyecto,
    get_dias, add_dia, update_dia, delete_dia,
    get_tareas, add_tarea, update_tarea, delete_tarea,
    get_max_fecha_dia  # <-- añade esto
)
from db import ensure_database, reset_database

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
        add_proyecto("", 99)  # nombre vacío, orden 99
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
    def __init__(self, mainwin):
        super().__init__()
        self.mainwin = mainwin
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

    def load_data(self, ref_fecha=None):
        if ref_fecha is None:
            ref_fecha = datetime.date.today()
        self.data = get_dias(ref_fecha)
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
        max_fecha = get_max_fecha_dia()
        if max_fecha:
            nueva_fecha = datetime.datetime.strptime(str(max_fecha), "%Y-%m-%d").date() + datetime.timedelta(days=1)
        else:
            nueva_fecha = datetime.date.today()
        add_dia(nueva_fecha.strftime("%Y-%m-%d"), 0, 0, 480)
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
    def __init__(self, mainwin):
        super().__init__()
        self.mainwin = mainwin
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.itemChanged.connect(self.save_changes)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_data(self, ref_fecha=None):
        if ref_fecha is None:
            ref_fecha = datetime.date.today()
        self.data = get_tareas(ref_fecha, order=1)
        # Evita que al rellenar la tabla se dispare itemChanged y provoque recursión
        self.table.blockSignals(True)
        proyectos = get_proyectos()
        dias = get_dias(self.mainwin.ref_fecha)
        fechas_disponibles = [str(d["fecha"]) for d in dias]
        self.table.setRowCount(len(self.data))
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Proyecto", "Fecha", "Descripción", "Prioridad", "Tiempo estimado", "Estado"
        ])
        for row, tarea in enumerate(self.data):
            # Proyecto: QComboBox editable (como antes)
            combo_proy = QComboBox()
            combo_proy.addItem("(Sin proyecto)", None)
            for p in proyectos:
                combo_proy.addItem(p["nombre"], p["id"])
            idxp = combo_proy.findData(tarea["proyecto_id"])
            combo_proy.setCurrentIndex(idxp if idxp >= 0 else 0)
            combo_proy.currentIndexChanged.connect(lambda idx, r=row, c=combo_proy: self.on_proyecto_changed(r, c))
            self.table.setCellWidget(row, 0, combo_proy)
            # Fecha
            combo_fecha = QComboBox()
            for f in fechas_disponibles:
                combo_fecha.addItem(f)
            # Selecciona la fecha actual de la tarea (si no está en la lista, la añade)
            f_actual = str(tarea["fecha"])
            if f_actual not in fechas_disponibles:
                combo_fecha.addItem(f_actual)
            combo_fecha.setCurrentText(f_actual)
            combo_fecha.currentIndexChanged.connect(lambda idx, r=row, c=combo_fecha: self.on_fecha_changed(r, c))
            self.table.setCellWidget(row, 1, combo_fecha)
            # Descripción
            item_desc = QTableWidgetItem(tarea["descripcion"])
            self.table.setItem(row, 2, item_desc)
            # Prioridad
            item_prio = QTableWidgetItem(str(tarea["prioridad"]))
            self.table.setItem(row, 3, item_prio)
            # Tiempo estimado
            item_tiempo = QTableWidgetItem(str(tarea["tiempo_estimado"]))
            self.table.setItem(row, 4, item_tiempo)
            # Estado
            combo_estado = QComboBox()
            combo_estado.addItem("Pendiente", "pendiente")
            combo_estado.addItem("Finalizado", "finalizada")
            # selecciona según valor en BD
            idx_estado = combo_estado.findData(tarea["estado"]) if tarea.get("estado") else 0
            combo_estado.setCurrentIndex(idx_estado if idx_estado >= 0 else 0)
            combo_estado.currentIndexChanged.connect(lambda idx, r=row, c=combo_estado: self.on_estado_changed(r, c))
            self.table.setCellWidget(row, 5, combo_estado)
        # Reactiva señales tras terminar de poblar la tabla
        self.table.blockSignals(False)

    def on_fecha_changed(self, row, combo_fecha):
        # Cambia solo la fecha de la tarea
        if row < 0:
            return
        tarea = self.data[row]
        nueva_fecha = combo_fecha.currentText()
        # Lee valores actuales en la fila para no perder ediciones pendientes
        desc_item = self.table.item(row, 2)
        prio_item = self.table.item(row, 3)
        time_item = self.table.item(row, 4)
        estado_combo = self.table.cellWidget(row, 5)
        estado_val = estado_combo.currentData() if estado_combo else tarea.get("estado")
        descripcion = desc_item.text() if desc_item else tarea["descripcion"]
        try:
            prioridad = int(prio_item.text()) if prio_item else tarea["prioridad"]
        except ValueError:
            prioridad = 99
        try:
            tiempo_estimado = int(time_item.text()) if time_item else tarea["tiempo_estimado"]
        except ValueError:
            tiempo_estimado = 0
        update_tarea(
            tarea["id"],
            tarea["proyecto_id"],
            nueva_fecha,
            descripcion,
            prioridad,
            tiempo_estimado,
            estado_val,
        )
        self.load_data(self.mainwin.ref_fecha)

    def on_estado_changed(self, row, combo_estado):
        # Cambia solo el estado de la tarea
        if row < 0:
            return
        tarea = self.data[row]
        nuevo_estado = combo_estado.currentData()
        fecha_combo = self.table.cellWidget(row, 1)
        fecha_val = fecha_combo.currentText() if fecha_combo else str(tarea["fecha"]) 
        # Lee valores actuales editados
        desc_item = self.table.item(row, 2)
        prio_item = self.table.item(row, 3)
        time_item = self.table.item(row, 4)
        descripcion = desc_item.text() if desc_item else tarea["descripcion"]
        try:
            prioridad = int(prio_item.text()) if prio_item else tarea["prioridad"]
        except ValueError:
            prioridad = 99
        try:
            tiempo_estimado = int(time_item.text()) if time_item else tarea["tiempo_estimado"]
        except ValueError:
            tiempo_estimado = 0
        update_tarea(
            tarea["id"],
            tarea["proyecto_id"],
            fecha_val,
            descripcion,
            prioridad,
            tiempo_estimado,
            nuevo_estado,
        )
        self.load_data(self.mainwin.ref_fecha)

    def on_proyecto_changed(self, row, combo_proy):
        # Cambia solo el proyecto de la tarea
        if row < 0:
            return
        tarea = self.data[row]
        nuevo_proyecto = combo_proy.currentData()
        # Lee valores actuales editados
        fecha_combo = self.table.cellWidget(row, 1)
        fecha_val = fecha_combo.currentText() if fecha_combo else str(tarea["fecha"]) 
        desc_item = self.table.item(row, 2)
        prio_item = self.table.item(row, 3)
        time_item = self.table.item(row, 4)
        estado_combo = self.table.cellWidget(row, 5)
        estado_val = estado_combo.currentData() if estado_combo else tarea.get("estado")
        descripcion = desc_item.text() if desc_item else tarea["descripcion"]
        try:
            prioridad = int(prio_item.text()) if prio_item else tarea["prioridad"]
        except ValueError:
            prioridad = 99
        try:
            tiempo_estimado = int(time_item.text()) if time_item else tarea["tiempo_estimado"]
        except ValueError:
            tiempo_estimado = 0
        update_tarea(
            tarea["id"],
            nuevo_proyecto,
            fecha_val,
            descripcion,
            prioridad,
            tiempo_estimado,
            estado_val,
        )
        self.load_data(self.mainwin.ref_fecha)
        
    def save_changes(self, item):
        row = item.row()
        col = item.column()
        # Solo procesar columnas: 2 (Descripción), 3 (Prioridad), 4 (Tiempo)
        if row < 0 or col not in (2, 3, 4):
            return
        tarea = self.data[row]
        # Recoge los valores actuales de la fila, comprobando que no sean None
        def get_text(r, c):
            cell = self.table.item(r, c)
            return cell.text() if cell else ""
        proyecto_id = tarea["proyecto_id"]
        # Fecha desde el combo
        combo_fecha = self.table.cellWidget(row, 1)
        fecha = combo_fecha.currentText() if combo_fecha else str(tarea["fecha"]) 
        descripcion = get_text(row, 2)
        try:
            prioridad = int(get_text(row, 3))
        except ValueError:
            prioridad = 99
        try:
            tiempo_estimado = int(get_text(row, 4))
        except ValueError:
            tiempo_estimado = 0
        # Estado desde el combo
        combo_estado = self.table.cellWidget(row, 5)
        estado = combo_estado.currentData() if combo_estado else tarea.get("estado", "pendiente")
        update_tarea(
            tarea["id"],
            proyecto_id,
            fecha,
            descripcion,
            prioridad,
            tiempo_estimado,
            estado
        )
        self.load_data(self.mainwin.ref_fecha)

# ------------------ MAIN ------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Planner de Proyectos")
        self.resize(1200, 600)

        # Widget superior: selector de fecha y flechas
        top_widget = QWidget()
        top_layout = QHBoxLayout()
        top_layout.addStretch()  # Espacio antes de los controles

        self.left_btn = QPushButton("←")
        self.right_btn = QPushButton("→")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setFixedWidth(130)  # Más ancho
        self.date_edit.setAlignment(Qt.AlignCenter)  # <-- Centra el texto

        top_layout.addWidget(self.left_btn)
        top_layout.addWidget(self.date_edit)
        top_layout.addWidget(self.right_btn)

        top_layout.addStretch()  # Espacio después de los controles
        top_widget.setLayout(top_layout)

        # Tabs
        self.tabs = QTabWidget()
        self.plan_tab = PlanificacionTab(self)
        self.dias_tab = DiasTab(self)
        self.proy_tab = ProyectosTab()
        self.tabs.addTab(self.plan_tab, "Planificación")
        self.tabs.addTab(self.dias_tab, "Días")
        self.tabs.addTab(self.proy_tab, "Proyectos")

        # Layout principal
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.addWidget(top_widget)
        main_layout.addWidget(self.tabs)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Eventos
        self.left_btn.clicked.connect(self.prev_day)
        self.right_btn.clicked.connect(self.next_day)
        self.date_edit.dateChanged.connect(self.on_date_changed)
        self.tabs.currentChanged.connect(self.on_tab_changed)  # <-- refresca al cambiar de pestaña

        self.ref_fecha = self.date_edit.date().toPyDate()
        self.update_tabs()

    def on_tab_changed(self, idx):
        self.update_tabs()

    def prev_day(self):
        self.ref_fecha -= datetime.timedelta(days=1)
        self.date_edit.setDate(QDate(self.ref_fecha))
        self.update_tabs()

    def next_day(self):
        self.ref_fecha += datetime.timedelta(days=1)
        self.date_edit.setDate(QDate(self.ref_fecha))
        self.update_tabs()

    def on_date_changed(self, qdate):
        self.ref_fecha = qdate.toPyDate()
        self.update_tabs()

    def update_tabs(self):
        self.plan_tab.load_data(self.ref_fecha)
        self.dias_tab.load_data(self.ref_fecha)
        self.proy_tab.load_data()  # <-- añade esto para actualizar ProyectosTab

if __name__=="__main__":
    if "--reset" in sys.argv:
        # full_reset_database ya no se usa; usar reset_database
        reset_database()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


