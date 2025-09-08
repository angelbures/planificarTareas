from PyQt5.QtCore import QDate, Qt
import sys, datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox, QDateEdit, QComboBox,
    QLabel, QSizePolicy
)
import datetime
from PyQt5.QtGui import QColor, QFont
from models import (
    get_proyectos, add_proyecto, update_proyecto, delete_proyecto,
    get_dias, add_dia, update_dia, delete_dia,
    get_tareas, add_tarea, update_tarea, delete_tarea,
    get_max_fecha_dia  # <-- añade esto
)
from db import ensure_database, reset_database

ensure_database()
def closeEvent(self, event):
    try:
        from models import export_all_tables_to_excel
        export_all_tables_to_excel('./' + datetime.date.today().strftime('%Y%m%d') + '-dump.xlsx')
    except Exception as e:
        try:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, 'Exportación', f'No se pudo exportar: {e}')
        except Exception:
            pass
    event.accept()
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
        self.MAX_NOMBRE_LEN = 30  # Límite según columna VARCHAR(30) en BBDD
        layout = QVBoxLayout()
        # Botones arriba
        btns = QHBoxLayout()
        add_btn = QPushButton("Añadir")
        del_btn = QPushButton("Borrar")
        # Alinear a la derecha y compactar
        btns.addStretch(1)
        btns.addWidget(add_btn)
        btns.addWidget(del_btn)
        try:
            add_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            del_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        except Exception:
            pass
        layout.addLayout(btns)

        # Tabla debajo
        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked)
        layout.addWidget(self.table)

        add_btn.clicked.connect(self.add)
        del_btn.clicked.connect(self.delete)
        self.table.itemChanged.connect(self.save_changes)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        # Entrar en edición con un solo clic también al hacer click en la celda (mouse press)
        self.table.cellClicked.connect(self.on_cell_clicked)

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
        # Anchos de columna: Nombre más ancho
        try:
            self.table.setColumnWidth(0, 60)   # ID
            self.table.setColumnWidth(1, 400)  # Nombre
            self.table.setColumnWidth(2, 80)   # Orden
        except Exception:
            pass

    def add(self):
        # Crear nuevo proyecto al final: orden = max(orden) + 10
        add_proyecto("", None)
        self.load_data()
        # Seleccionar la última fila y editar el nombre directamente
        try:
            last_row = self.table.rowCount() - 1
            if last_row >= 0:
                self.table.setCurrentCell(last_row, 1)
                item = self.table.item(last_row, 1)
                if item is None:
                    item = QTableWidgetItem("")
                    self.table.setItem(last_row, 1, item)
                self.table.editItem(item)
        except Exception:
            pass

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
        nombre_item = self.table.item(row,1)
        nombre = nombre_item.text() if nombre_item else ""
        # Validación longitud nombre para no superar la BBDD
        if len(nombre) > self.MAX_NOMBRE_LEN:
            QMessageBox.warning(self, "Nombre demasiado largo",
                                f"El nombre excede {self.MAX_NOMBRE_LEN} caracteres y será recortado.")
            nombre = nombre[:self.MAX_NOMBRE_LEN]
            # Reflejar recorte en la UI
            self.table.blockSignals(True)
            self.table.setItem(row,1,QTableWidgetItem(nombre))
            self.table.blockSignals(False)
        orden = int(self.table.item(row,2).text())
        update_proyecto(id, nombre, orden)
        self.load_data()

    def on_selection_changed(self):
        # Si se selecciona una celda de Nombre (1) u Orden (2), entrar en edición con un clic
        sel = self.table.selectedIndexes()
        if not sel:
            return
        idx = sel[0]
        if idx.column() in (1, 2):
            item = self.table.item(idx.row(), 1)
            if idx.column() == 2:
                item = self.table.item(idx.row(), 2)
            if item is None:
                item = QTableWidgetItem("")
                self.table.setItem(idx.row(), idx.column(), item)
            # Forzar edición inmediata
            self.table.editItem(item)

    def on_cell_clicked(self, row, column):
        # Entrada inmediata a edición con un solo clic en Nombre u Orden
        if column in (1, 2):
            item = self.table.item(row, column)
            if item is None:
                item = QTableWidgetItem("")
                self.table.setItem(row, column, item)
            self.table.editItem(item)

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
        # Barra superior con botón de orden
        top_bar = QHBoxLayout()
        self.btn_toggle_order = QPushButton("Orden: Fecha/Prioridad")
        self.btn_toggle_order.setToolTip("Alternar orden entre Fecha+Prioridad y Proyecto+Prio+Fecha")
        self.btn_toggle_order.clicked.connect(self.toggle_order)
        top_bar.addWidget(self.btn_toggle_order)
        top_bar.addStretch(1)
        layout.addLayout(top_bar)

        # 1 = por fecha,prioridad; 2 = por proyecto, prio, fecha
        self.order_mode = 1
        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.table.itemChanged.connect(self.save_changes)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_data(self, ref_fecha=None):
        if ref_fecha is None:
            ref_fecha = datetime.date.today()
        self.data = get_tareas(ref_fecha, order=self.order_mode)
        # Evita que al rellenar la tabla se dispare itemChanged y provoque recursión
        self.table.blockSignals(True)
        proyectos = get_proyectos()
        dias = get_dias(self.mainwin.ref_fecha)
        fechas_disponibles = [str(d["fecha"]) for d in dias]
        self.table.setRowCount(len(self.data))
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Proyecto", "Fecha", "Descripción", "Prio", "Tiempo", "Estado"
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
            item_prio.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, item_prio)
            # Tiempo estimado
            item_tiempo = QTableWidgetItem(str(tarea["tiempo_estimado"]))
            item_tiempo.setTextAlignment(Qt.AlignCenter)
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

            # Estilo visual para finalizadas: tachado y verde tenue
            es_finalizada = (tarea.get("estado") == "finalizada")
            if es_finalizada:
                verde_tenue = QColor(200, 240, 200)
                font_strike = QFont()
                font_strike.setStrikeOut(True)
                # Aplica a columnas 0..5
                for col in range(6):
                    w = self.table.cellWidget(row, col)
                    if w is not None:
                        w.setStyleSheet("background-color: rgb(200,240,200);")
                    else:
                        item = self.table.item(row, col)
                        if item is not None:
                            item.setBackground(verde_tenue)
                            item.setFont(font_strike)
        # Reactiva señales tras terminar de poblar la tabla
        self.table.blockSignals(False)

        # Ajustes de ancho de columnas (aprox. píxeles, 1 char ~ 8 px)
        # Proyecto ~25 chars, Descripción ~75 chars, Prio/Tiempo estrechas
        try:
            self.table.setColumnWidth(0, 25 * 8)   # Proyecto
            self.table.setColumnWidth(2, 75 * 8)   # Descripción
            self.table.setColumnWidth(3, 9 * 8)    # Prio
            self.table.setColumnWidth(4, 10 * 8)   # Tiempo
        except Exception:
            pass

    def toggle_order(self):
        # Alterna entre 1 (fecha, prioridad) y 2 (proyecto, prio, fecha)
        self.order_mode = 2 if self.order_mode == 1 else 1
        self.btn_toggle_order.setText(
            "Orden: Proyecto/Prio/Fecha" if self.order_mode == 2 else "Orden: Fecha/Prioridad"
        )
        # recarga con la fecha de referencia del main
        self.load_data(self.mainwin.ref_fecha)

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
class PlanDiaTab(QWidget):
    def __init__(self, mainwin):
        super().__init__()
        self.mainwin = mainwin
        self.order_mode = 1  # 1: fecha/prio, 2: proyecto/prio/fecha
        self.active_grid = 'tareas'

        main_layout = QVBoxLayout()

        # Barra superior común: botón de orden y acciones Añadir/Borrar según foco
        top_bar = QHBoxLayout()
        self.btn_toggle_order = QPushButton("Orden: Fecha/Prioridad")
        self.btn_toggle_order.setToolTip("Alternar orden entre Fecha+Prioridad y Proyecto+Prio+Fecha")
        self.btn_toggle_order.clicked.connect(self.toggle_order)
        top_bar.addWidget(self.btn_toggle_order)

        top_bar.addStretch(1)
        self.add_btn = QPushButton("Añadir")
        self.dup_btn = QPushButton("Duplicar tarea")
        self.del_btn = QPushButton("Borrar")
        self.add_btn.clicked.connect(self.add_focused)
        self.dup_btn.clicked.connect(self.duplicar_tarea)
        self.del_btn.clicked.connect(self.delete_focused)
        top_bar.addWidget(self.add_btn)
        top_bar.addWidget(self.dup_btn)
        top_bar.addWidget(self.del_btn)
        main_layout.addLayout(top_bar)

        # Tablas lado a lado con títulos
        self.tareas_table = QTableWidget()
        self.tareas_table.verticalHeader().setVisible(False)
        self.tareas_table.itemChanged.connect(self.tarea_item_changed)
        self.tareas_table.itemSelectionChanged.connect(lambda: self.set_active_grid('tareas'))

        self.dias_table = QTableWidget()
        self.dias_table.verticalHeader().setVisible(False)
        self.dias_table.itemChanged.connect(self.dia_item_changed)
        self.dias_table.itemSelectionChanged.connect(lambda: self.set_active_grid('dias'))

        content_layout = QHBoxLayout()
        left_box = QVBoxLayout()
        right_box = QVBoxLayout()

        lbl_tareas = QLabel("Tareas")
        lbl_dias = QLabel("Días")
        left_box.addWidget(lbl_tareas)
        left_box.addWidget(self.tareas_table)
        right_box.addWidget(lbl_dias)
        right_box.addWidget(self.dias_table)

        content_layout.addLayout(left_box, 1)
        content_layout.addLayout(right_box, 1)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

        # datasets
        self.tareas_data = []
        self.proyectos = []
        self.dias_data = []

        # Estilos de foco iniciales
        self.set_active_grid('tareas')

    def set_active_grid(self, which):
        self.active_grid = which
        # Resalta el grid activo con borde
        active_style = "QTableWidget{border:2px solid rgb(0,120,215);}"
        inactive_style = "QTableWidget{border:1px solid rgb(200,200,200);}"
        self.tareas_table.setStyleSheet(active_style if which=='tareas' else inactive_style)
        self.dias_table.setStyleSheet(active_style if which=='dias' else inactive_style)

    # ----- Carga de datos -----
    def load_data(self, ref_fecha=None):
        if ref_fecha is None:
            ref_fecha = datetime.date.today()
        # Poblar tareas
        self._load_tareas(ref_fecha)
        # Poblar días
        self._load_dias(ref_fecha)

    def _load_tareas(self, ref_fecha):
        self.tareas_data = get_tareas(ref_fecha, order=self.order_mode)
        self.proyectos = get_proyectos()
        dias = get_dias(self.mainwin.ref_fecha)
        fechas_disponibles = [str(d["fecha"]) for d in dias]

        self.tareas_table.blockSignals(True)
        self.tareas_table.setRowCount(len(self.tareas_data))
        self.tareas_table.setColumnCount(6)
        self.tareas_table.setHorizontalHeaderLabels(["Proyecto", "Fecha", "Descripción", "Prio", "Tiempo", "Estado"])

        for row, tarea in enumerate(self.tareas_data):
            # Proyecto
            combo_proy = QComboBox()
            combo_proy.addItem("(Sin proyecto)", None)
            for p in self.proyectos:
                combo_proy.addItem(p["nombre"], p["id"])
            idxp = combo_proy.findData(tarea["proyecto_id"])
            combo_proy.setCurrentIndex(idxp if idxp >= 0 else 0)
            combo_proy.currentIndexChanged.connect(lambda idx, r=row, c=combo_proy: self.on_tarea_proyecto_changed(r, c))
            self.tareas_table.setCellWidget(row, 0, combo_proy)

            # Fecha
            combo_fecha = QComboBox()
            for f in fechas_disponibles:
                combo_fecha.addItem(f)
            f_actual = str(tarea["fecha"])
            if f_actual not in fechas_disponibles:
                combo_fecha.addItem(f_actual)
            combo_fecha.setCurrentText(f_actual)
            combo_fecha.currentIndexChanged.connect(lambda idx, r=row, c=combo_fecha: self.on_tarea_fecha_changed(r, c))
            self.tareas_table.setCellWidget(row, 1, combo_fecha)

            # Descripción
            item_desc = QTableWidgetItem(tarea["descripcion"])
            self.tareas_table.setItem(row, 2, item_desc)
            # Prio
            item_prio = QTableWidgetItem(str(tarea["prioridad"]))
            item_prio.setTextAlignment(Qt.AlignCenter)
            self.tareas_table.setItem(row, 3, item_prio)
            # Tiempo
            item_tiempo = QTableWidgetItem(str(tarea["tiempo_estimado"]))
            item_tiempo.setTextAlignment(Qt.AlignCenter)
            self.tareas_table.setItem(row, 4, item_tiempo)
            # Estado
            combo_estado = QComboBox()
            combo_estado.addItem("Pendiente", "pendiente")
            combo_estado.addItem("Finalizado", "finalizada")
            idx_estado = combo_estado.findData(tarea.get("estado")) if tarea.get("estado") else 0
            combo_estado.setCurrentIndex(idx_estado if idx_estado >= 0 else 0)
            combo_estado.currentIndexChanged.connect(lambda idx, r=row, c=combo_estado: self.on_tarea_estado_changed(r, c))
            self.tareas_table.setCellWidget(row, 5, combo_estado)

            # Estilo finalizada
            es_finalizada = (tarea.get("estado") == "finalizada")
            if es_finalizada:
                verde_tenue = QColor(200, 240, 200)
                font_strike = QFont()
                font_strike.setStrikeOut(True)
                for col in range(6):
                    w = self.tareas_table.cellWidget(row, col)
                    if w is not None:
                        w.setStyleSheet("background-color: rgb(200,240,200);")
                    else:
                        item = self.tareas_table.item(row, col)
                        if item is not None:
                            item.setBackground(verde_tenue)
                            item.setFont(font_strike)

        self.tareas_table.blockSignals(False)
        # Ajustes ancho
        try:
            self.tareas_table.setColumnWidth(0, 25*8)
            self.tareas_table.setColumnWidth(2, 75*8)
            self.tareas_table.setColumnWidth(3, 9*8)
            self.tareas_table.setColumnWidth(4, 10*8)
        except Exception:
            pass

    def _load_dias(self, ref_fecha):
        self.dias_data = get_dias(ref_fecha)
        self.dias_table.blockSignals(True)
        self.dias_table.setRowCount(len(self.dias_data))
        self.dias_table.setColumnCount(7)
        # Títulos más cortos
        self.dias_table.setHorizontalHeaderLabels(["Fecha","Reun","Expl","Max","Disp","Suma","Dif"])
        for r,d in enumerate(self.dias_data):
            # Fecha con QDateEdit (editable, centrado)
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            # QDate.fromString con formato ISO
            date_edit.setDisplayFormat("yyyy-MM-dd")
            # Establecer la fecha actual del registro
            try:
                y,m,day = map(int, str(d["fecha"]).split("-"))
                date_edit.setDate(QDate(y, m, day))
            except Exception:
                date_edit.setDate(QDate.currentDate())
            # Señal de cambio
            date_edit.dateChanged.connect(lambda qd, row=r, w=None: self.on_dia_fecha_changed(row, qd))
            self.dias_table.setCellWidget(r, 0, date_edit)
            # HH:MM centrados
            def itm_hhmm(val, editable=True):
                it = QTableWidgetItem(minutos_a_hhmm(val))
                it.setTextAlignment(Qt.AlignCenter)
                if not editable:
                    it.setFlags(it.flags() & ~0x2)
                return it
            self.dias_table.setItem(r,1, itm_hhmm(d["reuniones"]))
            self.dias_table.setItem(r,2, itm_hhmm(d["explotacion"]))
            self.dias_table.setItem(r,3, itm_hhmm(d["maximo"]))
            self.dias_table.setItem(r,4, itm_hhmm(d["disponible"], editable=False))
            self.dias_table.setItem(r,5, itm_hhmm(d["suma_tareas"], editable=False))
            # Diferencia con signo: -HH:MM si negativa
            diff = d["disponible"] - d["suma_tareas"]
            abs_txt = minutos_a_hhmm(abs(diff))
            txt = ("-" + abs_txt) if diff < 0 else abs_txt
            diff_item = QTableWidgetItem(txt)
            diff_item.setTextAlignment(Qt.AlignCenter)
            if diff < 0:
                diff_item.setBackground(QColor(255,230,180))
            diff_item.setFlags(diff_item.flags() & ~0x2)
            self.dias_table.setItem(r,6,diff_item)
        self.dias_table.blockSignals(False)
        # Anchos ajustados: fecha y HH:MM compactos; tabla de días lo más estrecha posible
        try:
            fecha_w = 90  # ~10 chars
            hhmm_w = 60   # ~7 chars con márgenes
            self.dias_table.setColumnWidth(0, fecha_w)
            for c in (1,2,3,4,5,6):
                self.dias_table.setColumnWidth(c, hhmm_w)
            total_w = fecha_w + 6*hhmm_w + 4
            self.dias_table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
            self.dias_table.setFixedWidth(total_w)
        except Exception:
            pass

    # ----- Handlers Tareas -----
    def on_tarea_proyecto_changed(self, row, combo_proy):
        if row < 0:
            return
        t = self.tareas_data[row]
        nuevo_proyecto = combo_proy.currentData()
        fecha_combo = self.tareas_table.cellWidget(row, 1)
        fecha_val = fecha_combo.currentText() if fecha_combo else str(t["fecha"]) 
        desc_item = self.tareas_table.item(row, 2)
        prio_item = self.tareas_table.item(row, 3)
        time_item = self.tareas_table.item(row, 4)
        estado_combo = self.tareas_table.cellWidget(row, 5)
        estado_val = estado_combo.currentData() if estado_combo else t.get("estado")
        descripcion = desc_item.text() if desc_item else t["descripcion"]
        try:
            prioridad = int(prio_item.text()) if prio_item else t["prioridad"]
        except ValueError:
            prioridad = 99
        try:
            tiempo = int(time_item.text()) if time_item else t["tiempo_estimado"]
        except ValueError:
            tiempo = 0
        update_tarea(t["id"], nuevo_proyecto, fecha_val, descripcion, prioridad, tiempo, estado_val)
        self.load_data(self.mainwin.ref_fecha)

    def on_tarea_fecha_changed(self, row, combo_fecha):
        if row < 0:
            return
        t = self.tareas_data[row]
        nueva_fecha = combo_fecha.currentText()
        desc_item = self.tareas_table.item(row, 2)
        prio_item = self.tareas_table.item(row, 3)
        time_item = self.tareas_table.item(row, 4)
        estado_combo = self.tareas_table.cellWidget(row, 5)
        estado_val = estado_combo.currentData() if estado_combo else t.get("estado")
        descripcion = desc_item.text() if desc_item else t["descripcion"]
        try:
            prioridad = int(prio_item.text()) if prio_item else t["prioridad"]
        except ValueError:
            prioridad = 99
        try:
            tiempo = int(time_item.text()) if time_item else t["tiempo_estimado"]
        except ValueError:
            tiempo = 0
        update_tarea(t["id"], t["proyecto_id"], nueva_fecha, descripcion, prioridad, tiempo, estado_val)
        self.load_data(self.mainwin.ref_fecha)

    def on_tarea_estado_changed(self, row, combo_estado):
        if row < 0:
            return
        t = self.tareas_data[row]
        nuevo_estado = combo_estado.currentData()
        fecha_combo = self.tareas_table.cellWidget(row, 1)
        fecha_val = fecha_combo.currentText() if fecha_combo else str(t["fecha"]) 
        desc_item = self.tareas_table.item(row, 2)
        prio_item = self.tareas_table.item(row, 3)
        time_item = self.tareas_table.item(row, 4)
        descripcion = desc_item.text() if desc_item else t["descripcion"]
        try:
            prioridad = int(prio_item.text()) if prio_item else t["prioridad"]
        except ValueError:
            prioridad = 99
        try:
            tiempo = int(time_item.text()) if time_item else t["tiempo_estimado"]
        except ValueError:
            tiempo = 0
        update_tarea(t["id"], t["proyecto_id"], fecha_val, descripcion, prioridad, tiempo, nuevo_estado)
        self.load_data(self.mainwin.ref_fecha)

    def tarea_item_changed(self, item):
        row = item.row(); col = item.column()
        if row < 0 or col not in (2,3,4):
            return
        t = self.tareas_data[row]
        def get_text(r,c):
            cell = self.tareas_table.item(r,c)
            return cell.text() if cell else ""
        combo_fecha = self.tareas_table.cellWidget(row, 1)
        fecha = combo_fecha.currentText() if combo_fecha else str(t["fecha"]) 
        desc = get_text(row,2)
        try:
            prio = int(get_text(row,3))
        except ValueError:
            prio = 99
        try:
            tiempo = int(get_text(row,4))
        except ValueError:
            tiempo = 0
        combo_estado = self.tareas_table.cellWidget(row, 5)
        estado = combo_estado.currentData() if combo_estado else t.get("estado","pendiente")
        update_tarea(t["id"], t["proyecto_id"], fecha, desc, prio, tiempo, estado)
        self.load_data(self.mainwin.ref_fecha)

    # ----- Handlers Días -----
    def dia_item_changed(self, item):
        row = item.row()
        if row < 0:
            return
        d = self.dias_data[row]
        # Columna 0 ahora la gestiona on_dia_fecha_changed
        fecha = d["fecha"]
        def to_min(r,c):
            cell = self.dias_table.item(r,c)
            return hhmm_a_minutos(cell.text()) if cell else 0
        reuniones = to_min(row,1)
        explotacion = to_min(row,2)
        maximo = to_min(row,3)
        update_dia(fecha, reuniones, explotacion, maximo)
        self.load_data(self.mainwin.ref_fecha)

    def on_dia_fecha_changed(self, row, qdate):
        if row < 0:
            return
        d = self.dias_data[row]
        nueva_fecha = qdate.toString("yyyy-MM-dd")
        # Conserva valores actuales de la fila
        def to_min(r,c):
            cell = self.dias_table.item(r,c)
            return hhmm_a_minutos(cell.text()) if cell else 0
        reuniones = to_min(row,1)
        explotacion = to_min(row,2)
        maximo = to_min(row,3)
        try:
            delete_dia(d["fecha"])  # eliminar PK antigua
            add_dia(nueva_fecha, reuniones, explotacion, maximo)  # insertar nueva fila
        except Exception:
            # Revertir visualmente si falla
            self._load_dias(self.mainwin.ref_fecha)
            return
        self.load_data(self.mainwin.ref_fecha)

    # ----- Botones -----
    def add_focused(self):
        if self.active_grid == 'tareas':
            # Añadir tarea con la fecha máxima existente en tabla 'dias'
            max_fecha = get_max_fecha_dia()
            fecha_ref = str(max_fecha) if max_fecha else str(self.mainwin.ref_fecha)
            add_tarea(None, fecha_ref, "", 99, 0)
        else:
            # Añadir día como en pestaña original
            max_fecha = get_max_fecha_dia()
            if max_fecha:
                nueva_fecha = datetime.datetime.strptime(str(max_fecha), "%Y-%m-%d").date() + datetime.timedelta(days=1)
            else:
                nueva_fecha = datetime.date.today()
            add_dia(nueva_fecha.strftime("%Y-%m-%d"), 0, 0, 480)
        self.load_data(self.mainwin.ref_fecha)

    def delete_focused(self):
        if self.active_grid == 'tareas':
            row = self.tareas_table.currentRow()
            if row < 0:
                return
            t = self.tareas_data[row]
            if QMessageBox.question(self, "Borrar", "¿Borrar esta tarea?") == QMessageBox.Yes:
                delete_tarea(t["id"])
                self.load_data(self.mainwin.ref_fecha)
        else:
            row = self.dias_table.currentRow()
            if row < 0:
                return
            d = self.dias_data[row]
            if QMessageBox.question(self, "Borrar", "¿Borrar este día?") == QMessageBox.Yes:
                delete_dia(d["fecha"])
                self.load_data(self.mainwin.ref_fecha)

    def toggle_order(self):
        self.order_mode = 2 if self.order_mode == 1 else 1
        self.btn_toggle_order.setText("Orden: Proyecto/Prio/Fecha" if self.order_mode == 2 else "Orden: Fecha/Prioridad")
        self._load_tareas(self.mainwin.ref_fecha)

    def duplicar_tarea(self):
        # Duplica la tarea seleccionada en el grid de tareas.
        # Reglas: mismo proyecto; el resto como una nueva tarea (descripcion vacía, prio 99, tiempo 0)
        row = getattr(self, 'tareas_table', None).currentRow() if hasattr(self, 'tareas_table') else -1
        if row is None or row < 0:
            return
        if not hasattr(self, 'tareas_data') or row >= len(self.tareas_data):
            return
        tarea = self.tareas_data[row]

        # Determinar fecha objetivo como hace add_focused para tareas: fecha máxima de días o ref actual
        max_fecha = get_max_fecha_dia()
        fecha_ref = str(max_fecha) if max_fecha else str(self.mainwin.ref_fecha)

        proyecto_id = tarea.get("proyecto_id")
        # Crear nueva tarea con mismos proyecto y fecha calculada, resto por defecto
        add_tarea(proyecto_id, fecha_ref, "", 99, 0)
        self.load_data(self.mainwin.ref_fecha)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Planner de Proyectos")
        # Ventana un 20% más grande que el valor anterior aproximado
        self.resize(1800, 1020)

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
        self.plan_dia_tab = PlanDiaTab(self)
        self.proy_tab = ProyectosTab()
        self.tabs.addTab(self.plan_dia_tab, "Planificación/Días")
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
        self.plan_dia_tab.load_data(self.ref_fecha)
        self.proy_tab.load_data()  # <-- añade esto para actualizar ProyectosTab

    def closeEvent(self, event):
        """Se ejecuta al cerrar la ventana para exportar los datos a Excel."""
        try:
            from models import export_all_tables_to_excel
            filename = f"./{datetime.date.today().strftime('%Y%m%d')}-dump.xlsx"
            export_all_tables_to_excel(filename)
        except Exception as e:
            QMessageBox.warning(self, 'Error en Exportación', f'No se pudo exportar a Excel: {e}')
        
        # Aceptar el evento para que la ventana se cierre
        event.accept()

if __name__=="__main__":
    if "--reset" in sys.argv:
        # full_reset_database ya no se usa; usar reset_database
        reset_database()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())






