from pathlib import Path
from services.library_service import LibraryService


def mostrar_menu():
    print("\n📚 MENÚ PRINCIPAL — Alejandría 🏛️")
    print("1. Registrar usuario")
    print("2. Subir libro (sin archivo)")
    print("3. Subir libro (con PDF/EPUB)")
    print("4. Listar libros disponibles")
    print("5. Tomar un libro prestado")
    print("6. Devolver libro")
    print("7. Escribir reseña")
    print("8. Ver vista previa de un libro")
    print("9. Ver préstamos activos")
    print("10. Abrir libro en préstamo 📖")
    print("11. Salir")
    return input("Seleccione una opción: ")


def main():
    print("📖 Bienvenido a Alejandría, la biblioteca en la nube 🏛️")
    library = LibraryService()

    # Establece las rutas base para los libros por defecto
    base = Path(__file__).resolve().parent / "data"
    quijote_path = base / "Don_Quijote_de_la_Mancha.pdf"
    frankenstein_path = base / "Frankenstein.pdf"

    # Intenta cargar algunos libros por defecto
    try:
        if quijote_path.exists():
            library.upload_book("Don Quijote de la Mancha", "Miguel de Cervantes", file_path=str(quijote_path))
        if frankenstein_path.exists():
            library.upload_book("Frankenstein", "Mary Shelley", file_path=str(frankenstein_path))
    except Exception as e:
        print(f"⚠️ Error inicializando libros: {e}")

    # Bucle principal del menú
    while True:
        opcion = mostrar_menu()

        # Registrar usuario
        if opcion == "1":
            nombre = input("Ingrese el nombre de usuario: ")
            result = library.register_user(nombre)
            print(result if isinstance(result, str) else f"🧍 Usuario '{result.username}' registrado correctamente.")

        # Subir libro sin archivo
        elif opcion == "2":
            titulo = input("Título del libro: ")
            autor = input("Autor: ")
            library.upload_book(titulo, autor)
            print(f"📘 Libro '{titulo}' subido correctamente (sin archivo).")

        # Subir libro con archivo
        elif opcion == "3":
            from tkinter import Tk, filedialog

            title = input("Título del libro: ")
            author = input("Autor: ")

            # Ocultar ventana principal de Tk
            root = Tk()
            root.withdraw()

            print("📂 Selecciona el archivo del libro (PDF o EPUB)...")
            file_path = filedialog.askopenfilename(
                title="Selecciona el archivo del libro",
                filetypes=[("Ebooks", "*.pdf *.epub"), ("Todos los archivos", "*.*")]
            )

            if not file_path:
                print("❌ No se seleccionó ningún archivo.")
            else:
                book = library.upload_book(title, author, True, file_path)
                print(f"📚 Libro '{book.title}' subido correctamente con: {book.file_path}")

        # Listar libros
        elif opcion == "4":
            print("\n📚 Libros en la biblioteca:")
            libros = library.list_books()
            if not libros:
                print("No hay libros en la biblioteca aún.")
            for b in libros:
                estado = "✅ Disponible" if b.available else "❌ Prestado"
                print(f" - {b.title} ({b.author}) [{estado}]")

        # Tomar libro prestado
        elif opcion == "5":
            usuario = input("Nombre del usuario: ")
            titulo = input("Título del libro: ")
            print(library.borrow_book(usuario, titulo))

        # Devolver libro
        elif opcion == "6":
            usuario = input("Nombre del usuario: ")
            titulo = input("Título del libro: ")
            print(library.return_book(usuario, titulo))

        # Escribir reseña
        elif opcion == "7":
            usuario = input("Nombre del usuario: ")
            titulo = input("Título del libro: ")
            comentario = input("Escriba su reseña: ")
            try:
                puntuacion = int(input("Puntuación (1-5): "))
            except ValueError:
                print("⚠️ Introduzca un número entre 1 y 5.")
                continue
            print(library.review_book(usuario, titulo, comentario, puntuacion))

        # Vista previa del libro
        elif opcion == "8":
            titulo = input("Título del libro: ")
            print(library.preview_book(titulo))

        # Ver préstamos activos
        elif opcion == "9":
            print("\n📑 Préstamos activos:")
            print(library.list_active_reservations())

        # Abrir libro en préstamo
        elif opcion == "10":
            usuario = input("Nombre del usuario: ")
            titulo = input("Título del libro: ")
            print(library.open_borrowed_book(usuario, titulo))

        # Salir
        elif opcion == "11":
            print("👋 Gracias por visitar Alejandría. ¡Hasta la próxima!")
            break

        else:
            print("❌ Opción no válida. Intente de nuevo.")


if __name__ == "__main__":
    main()
