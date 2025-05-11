from herramientas.medical_agent import MedicalAgent
import json
import os
from datetime import datetime


def main():
    # Asegurar que existe la carpeta data_usuario
    os.makedirs("data_usuario", exist_ok=True)

    # Inicializar el agente médico
    agent = MedicalAgent(
        user_data_dir="data_usuario", medical_info_file="medical_info.json"
    )

    # Verificar si existe medical_info.json
    medical_info_path = os.path.join("data_usuario", "medical_info.json")
    if os.path.exists(medical_info_path):
        print(f"Archivo medical_info.json encontrado en {medical_info_path}")
        try:
            with open(medical_info_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                print(
                    f"Información médica cargada para: {existing_data.get('nombre', 'Usuario desconocido')}"
                )
                print(
                    f"Última actualización: {existing_data.get('ultima_actualizacion', 'Desconocida')}"
                )
        except Exception as e:
            print(f"Error al leer el archivo: {str(e)}")
    else:
        print(
            "Archivo medical_info.json no encontrado. Se creará uno nuevo con datos de ejemplo."
        )
        # Datos de ejemplo del usuario (solo para crear uno nuevo si no existe)
        user_data = {
            "id": "usuario_ejemplo",
            "nombre": "Usuario Ejemplo",
            "edad": 35,
            "peso": 70,
            "altura": 175,
            "genero": "no especificado",
            "fecha_nacimiento": "1990-01-01",
            "grupo_sanguineo": "O+",
            "condiciones_medicas": ["Ejemplo de condición médica"],
            "alergias": ["Ejemplo de alergia"],
            "medicamentos": [
                {
                    "nombre": "Ejemplo de medicamento",
                    "dosis": "10mg",
                    "frecuencia": "Una vez al día",
                    "motivo": "Ejemplo",
                }
            ],
        }
        # Guardar el historial médico para crear el archivo
        agent._save_user_medical_data(user_data)
        print(f"Se ha creado un archivo de ejemplo para {user_data['nombre']}")

    # Recuperar datos médicos actuales
    print("\nRecuperando datos médicos...")
    medical_data = agent.get_user_medical_data()
    if medical_data:
        print(f"Datos médicos encontrados: {medical_data['nombre']}")
        print(
            f"Condiciones médicas: {', '.join(medical_data.get('condiciones_medicas', []))}"
        )
        print(f"Medicamentos: {len(medical_data.get('medicamentos', []))}")
    else:
        print("No se encontraron datos médicos.")

    # Realizar una consulta médica
    print("\nRealizando consulta médica...")
    consulta = "¿Cuáles son mis medicamentos y para qué sirven?"
    respuesta = agent.process_with_user_data(consulta)
    print(f"Respuesta: {respuesta}\n")

    # Añadir un nuevo estudio médico de ejemplo
    print("\nAñadiendo un nuevo estudio médico de ejemplo...")
    nuevo_estudio = {
        "tipo": "estudio",
        "nombre": "Ejemplo de estudio",
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "resultado": "Resultados normales",
        "notas": "Estudio añadido como ejemplo",
    }
    # Preguntar al usuario si desea añadir este estudio
    respuesta = input("¿Desea añadir un estudio médico de ejemplo? (s/n): ")
    if respuesta.lower() == "s":
        if agent.add_medical_record(medical_record=nuevo_estudio):
            print("Estudio médico añadido correctamente.")
        else:
            print("Error al añadir el estudio médico.")
    else:
        print("No se añadió ningún estudio médico.")

    # Mostrar el historial médico actualizado
    print("\nHistorial médico actualizado:")
    medical_data = agent.get_user_medical_data()
    if medical_data:
        print(f"Nombre: {medical_data.get('nombre')}")
        print(f"Última actualización: {medical_data.get('ultima_actualizacion')}")
        print(f"Medicamentos: {len(medical_data.get('medicamentos', []))}")
        print(f"Estudios médicos: {len(medical_data.get('estudios_medicos', []))}")
        print(
            f"Consultas registradas: {len(medical_data.get('historial_consultas', []))}"
        )


if __name__ == "__main__":
    main()
