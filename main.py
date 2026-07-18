import sys, pandas, pymysql, qrcode, re, os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *


#Class 
class Aplicacion(QMainWindow):

    def __init__(self):
        #Constructor de la clase 
        super().__init__()
        #Mandar a llamar nuestra interfaz
        loadUi(r"/Users/esteban/Documents/Aplicacion/Interfaz.ui",self)
        self.btnRegistrar.clicked.connect(self.registrar)
        self.btnActualizar.clicked.connect(self.actualizar)
        self.btnEliminar.clicked.connect(self.eliminar)
        self.btnCancelar.clicked.connect(self.limpiar)
        self.btnExportar.clicked.connect(self.exportar)
        self.btnBuscar.clicked.connect(self.buscar)
        #Llamar a la funcion conexion desde el constructor
        self.conexion()
        #Validadores numericos no permiten agregar mas que numeros
        self.txtID.setValidator(QIntValidator())
        self.txtCelular.setValidator(QIntValidator())
        #Bloquear los botones al inciar la apalicacion
        self.estado_botones(False)
        #Bloquear boton 
        self.txtQR.setEnabled(False)
        self.mostrar_datos()

    def estado_botones(self,estado):
       self.btnEliminar.setEnabled(estado)
       self.btnActualizar.setEnabled(estado)

    def closeEvent(self, evento):
        try:
            #Crear la conexion 
            #Verificar si existe el atributo y si esta abierto 
            if hasattr(self,"c") and self.c.open:
                self.cur.close()
                self.c.close()
                print("Conexion cerrada cerrada desde close Event")
            else:
                print("No haia una conexion por cerrar")
        except Exception as error:
            QMessageBox.warning(self,"Error",str(error))

    def conexion(self):
        try:
            self.c = pymysql.connect(host="localhost",
                                     user="root",
                                     password="12345678",
                                     database="aplicacion")
            self.cur = self.c.cursor()
            QMessageBox.information(self,"Atencion","Conexion hecha con exito")

        except Exception as error:
            QMessageBox.warning(self,"Error",str(error))

    def registrar(self):
        #Metodo para crear un qr artificial
        #self.crear_qr("ESTUDIANTE","RABE111HACM34LSA")

       # Recuperar los datos del front
        try:
            paterno = self.txtPaterno.text().upper ()
            materno = self.txtMaterno.text().upper()
            nombre = self.txtNombre.text().upper()
            correo = self. txtCorreo.text().lower()
            celular = self.txtCelular.text()
            rol = self.cbRol.currentText()
            curp = self.txtCurp.text().upper()
            qr = rol + "-" + curp
            ruta = f"/Users/esteban/Documents/Aplicacion/QRS/{rol}/{rol}-{curp}.png"

        #Validar que todas las variables contengan informacion
            if len(paterno) == 0:
                QMessageBox.warning(self,"Atencion","Captura el apellido paterno")
                return
            elif len(materno) == 0:
                QMessageBox.warning(self,"Atencion","Captrua el apellido materno")
                return
            elif len(nombre) == 0:
                QMessageBox.warning(self,"Atencion","Captura el nombre")
                return
            elif len(correo) == 0:
                QMessageBox.warning(self,"Atencion","Captura el correo electronico")
                return
            elif len(celular) != 10:
                QMessageBox.warning(self,"Atencion","Captura el numero de celular")
                return
            elif len(rol) == "SELECCIONA UNA OPCION":
                QMessageBox.warning(self,"Atencion","Captura el rol del usuario")
                return
            elif len(curp) != 18:
                QMessageBox.warning(self,"Atencion","Captura la curp del usuario bajo 18 digitos")
                return
        
            validacionNombre = self.validar_nombre()

            if validacionNombre == False:
                QMessageBox.warning(self, "Atencion" , "Corroborar el nombre y el apellido")
                return
            
            validacionCorreo = self.validar_correo()

            if validacionCorreo == False:
                QMessageBox.warning(self, "Atencion", "Corroborar que el correo tenga el formato apropiado")
                return
            
            registro = '''
            INSERT INTO usuarios (paterno, materno, nombre, correo, celular, rol, curp, qr, ruta)
            VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}')
            '''.format(paterno, materno, nombre, correo, celular, rol, curp, qr, ruta)

            self.cur.execute(registro)
            self.c.commit()

            QMessageBox.information(self,"Atencion","Registro exitoso")

            self.limpiar()
            self.crear_qr(rol,curp)
            #Refescar la interfaz
            self.mostrar_datos()


        except Exception as error:
            QMessageBox.warning(self,"Error",str(error))

    def buscar(self):
        try:

            opcion = str(self.BusquedaBox.currentText())

            if opcion == "ID":
                texto_id = self.txtID.text().strip()
                if not texto_id.isdigit():
                    QMessageBox.warning(self, "Atencion", "Ingresa un ID válido")
                    return
                id = int(texto_id)
                consulta = "SELECT * FROM usuarios WHERE idusuario = %s" #Evitar inyeccion de sql
                self.cur.execute(consulta, (id,))

            elif opcion == "CURP":
                curp = self.txtCurp.text().upper().strip()
                if not curp:
                    QMessageBox.warning(self, "Atencion", "Ingresa un CURP válido")
                    return
                consulta = "SELECT * FROM usuarios WHERE curp = %s"
                self.cur.execute(consulta, (curp,))

            else:
                QMessageBox.warning(self, "Atencion", "Selecciona una opcion de busqueda")
                return
            
            resultado = self.cur.fetchone()
            #Verificar que la consulta exista 
            if resultado is None:
                QMessageBox.warning(self,"Atencion","No se encontro el registro")
                self.limpiar()
                self.estado_botones(False)
                return 
            self.txtID.setText(str(resultado[0]))
            self.txtPaterno.setText(resultado[1])
            self.txtMaterno.setText(resultado[2])
            self.txtNombre.setText(resultado[3])
            self.txtCorreo.setText(resultado[4]) 
            self.txtCelular.setText(resultado[5])

            if resultado[6] == "ADMINISTRATIVO":
                self.cbRol.setCurrentIndex(1)
            elif resultado[6] == "ESTUDIANTE":
                self.cbRol.setCurrentIndex(2)
            elif resultado[6] == "PROFESOR":
                self.cbRol.setCurrentIndex(3)
            elif resultado[6] == "EXTERNO":
                self.cbRol.setCurrentIndex(4)
            elif resultado[6] == "OPERATIVO":
                self.cbRol.setCurrentIndex(5)
            
            
            self.txtCurp.setText(resultado[7])
            self.txtQR.setText(resultado[8])
            self.estado_botones(True)
            self.txtID.setEnabled(False)

        except Exception as error:
            QMessageBox.warning(self,"Error",str(error))
       

    def actualizar(self):
        try:
          #Recuperar id, correo, numero del usuario 
          id = int(self.txtID.text())  
          correo = self.txtCorreo.text()
          celular = self.txtCelular.text()

          if len (correo) == 0:
              QMessageBox.warning(self,"Atencion","Captura el correo electronico")
              return
          
          validacioncorreo = self.validar_correo()

          if validacioncorreo == False:
            QMessageBox.warning(self,"Atencion","El nuevo correo no tiene el formato correcto")
            return
          
          if len(celular) != 10:
              QMessageBox.warning(self,"Atencion","El numero de celular debe tener 10 digitos")
              return
          #Proceso de actualizacion de datos

          actualizacion = '''
            UPDATE usuarios SET correo = '{}', celular = '{}' WHERE idusuario = {}
            '''.format(correo, celular, id)
          
          self.cur.execute(actualizacion)

          self.c.commit()

          #Mensaje
          QMessageBox.information(self,"Atencion","Actualizacion exitosa")

          self.limpiar()

          self.mostrar_datos()

        except Exception as error:
            QMessageBox.warning(self,"Error",str(error))
    
    def eliminar(self):
        try:
            respuesta = QMessageBox.question(self, "Atencion", 
                                             "¿Estas seguro de eliminar el registro?", 
                                             QMessageBox.Yes | QMessageBox.No)
            if respuesta == QMessageBox.Yes:
                texto_id = self.txtID.text().strip()
                if not texto_id.isdigit():
                    QMessageBox.warning(self, "Atencion", "Ingresa un ID válido")
                    return
                id = int(texto_id)

                self.cur.execute("SELECT ruta FROM usuarios WHERE idusuario = %s", (id,))
                resultado = self.cur.fetchone()

                if resultado:
                    ruta_archivo = resultado[0]
                    if ruta_archivo and os.path.exists(ruta_archivo):
                        os.remove(ruta_archivo)
                        print("Archivo eliminado:", ruta_archivo)
                    else:
                        print("El archivo no existe:", ruta_archivo)

                self.cur.execute("DELETE FROM usuarios WHERE idusuario = %s", (id,))
                self.c.commit()

                QMessageBox.information(self, "Atencion", "Eliminacion exitosa")
                self.limpiar()
                self.mostrar_datos()
            elif respuesta == QMessageBox.No:
                QMessageBox.information(self, "Atencion", "Eliminacion cancelada")
        except Exception as error:
            QMessageBox.warning(self, "Error", str(error))

    def limpiar(self):
        self.txtID.setEnabled(True)
        #Limpiar las cajas y seleccionar el index 0 de la combobox
        self.txtID.clear()
        self.txtPaterno.clear()
        self.txtMaterno.clear()
        self.txtNombre.clear()
        self.txtCorreo.clear()
        self.txtCelular.clear()
        self.cbRol.setCurrentIndex(0)
        self.txtCurp.clear()
        self.txtQR.clear()
        self.estado_botones(False)

    def exportar(self):
        try:
            #Variables con la cantida de filas y columnas
            cantidad_filas = self.tabla.rowCount()
            cantidad_columnas = self.tabla.columnCount()
            
            if cantidad_filas == 0:
                QMessageBox.warning(self,"Atencion","No hay datos para exportar")
                return
            
            columnas = (self.tabla.horizontalHeaderItem(i).text() 
                        for i in range(cantidad_columnas))
            
            #Arreglo general para guardar los datos de la tabla
            
            datos = []
            for fila in range(cantidad_filas):
                #Arreglo para guardar los datos de cada fila
                fila_datos = []
                for columna in range(cantidad_columnas):
                    celda = self.tabla.item(fila, columna)
                    if celda is not None:
                        fila_datos.append(celda.text())
                    else:
                        fila_datos.append("")
                datos.append(fila_datos)
            #print(datos)
            # Crear un DataFrame de pandas
            df = pandas.DataFrame(datos, columns=columnas)
            #Ruta donde guardar el dataframe
            ruta, _ = QFileDialog.getSaveFileName(self, 
                                                  "Guardar archivo", 
                                                  "",
                                                  "Archivos Excel (*.xlsx)")
            #print(ruta)
            if not ruta:
                return
            # Guardar el DataFrame en un archivo Excel
            df.to_excel(ruta, index=False)

        except Exception as error:
            QMessageBox.warning(self,"Error",str(error))


    def mostrar_datos(self):
        try:
            consulta = "SELECT * FROM usuarios"
            #Ejecutar la consulta
            self.cur.execute(consulta)
            #Obtener los resultados de la consulta
            resultado = self.cur.fetchall()
            #Agregar los resultados a la tabla
            self.tabla.setRowCount(len(resultado))
            
            for fila, datos in enumerate(resultado):
                for columna, dato in enumerate(datos):
                    self.tabla.setItem(fila, columna, QTableWidgetItem(str(dato)))

            #resultado se manda como una tubla de tuplas se cambia a listas 
            # y se recorren las filas como las listas y las columnas como 
            # las listas aniadadas
            # resultado = ((1,2,3,4,6,7),(1,2,3,4,,6,7))

            self.tabla.resizeColumnsToContents()

            
        except Exception as error:
            QMessageBox.warning(self,"Error",str(error))


    def crear_qr(self,rol,curp):
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L,)
        codigo = rol + "-" + curp
        qr.add_data(codigo)
        #Crear qr
        qr.make()
        qrimg = qr.make_image(fill_color="#000000",
                              back_color="#ffffff").convert("RGB")
        ruta = "/Users/esteban/Documents/Aplicacion/QRS"
        #Ruta dinamica para guardar el QR
        qrimg.save(f"{ruta}/{rol}/{codigo}.png")
        #Mensaje
        print("Codigo QR creado")


    
    def validar_nombre(self):
        texto = self.txtNombre.text() + self.txtPaterno.text() + self.txtMaterno.text()

        # Expresión regular que permite solo letras, tildes y espacios
        if re.match("^[A-Za-záéíóúÁÉÍÓÚüÜñÑ ]*$", texto):
            return True
        else:
            return False

    def validar_correo(self):
            # Obtener el texto del QLineEdit
            correo = self.txtCorreo.text()

            # Expresión regular para validar un correo electrónico
            patron = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            
            # Validar correo con el patrón
            if re.match(patron, correo):
                return True
            else:
                return False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    prototipo = Aplicacion()
    prototipo.show()
    app.exec()

