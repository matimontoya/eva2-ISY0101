from .agente import conversar


def main():
    print("ContaSimple IA")
    print("Usa /empresa ID para cambiar de empresa y /salir para cerrar.")

    while True:
        valor = input("ID de empresa: ").strip()
        try:
            empresa_id = int(valor)
            if empresa_id > 0:
                break
        except ValueError:
            pass
        print("Ingresa un número positivo, por ejemplo 1.")

    while True:
        pregunta = input(f"Empresa {empresa_id} > ").strip()

        if pregunta == "/salir":
            print("Chat cerrado.")
            break

        if pregunta.startswith("/empresa "):
            try:
                nuevo_id = int(pregunta.split(maxsplit=1)[1])
                if nuevo_id <= 0:
                    raise ValueError
                empresa_id = nuevo_id
                print(f"Ahora estás en el chat de la empresa {empresa_id}.")
            except (IndexError, ValueError):
                print("Formato: /empresa 2")
            continue

        if not pregunta:
            continue

        try:
            print(f"Agente > {conversar(empresa_id, pregunta)}")
        except Exception as error:
            detalle = str(error)
            if "RESOURCE_EXHAUSTED" in detalle or "quota" in detalle.lower():
                print(
                    "Gemini alcanzó el límite de solicitudes de tu cuota actual. "
                    "El agente podrá volver a responder cuando se renueve la cuota "
                    "o si habilitas un plan con más capacidad. No se procesó esta consulta."
                )
            else:
                print(
                    f"No se pudo completar la consulta ({type(error).__name__}). "
                    "Revisa la conexión y la configuración de Gemini e inténtalo más tarde."
                )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nChat cerrado.")
