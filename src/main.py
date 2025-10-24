from src.services.library_service import LibraryService

def main():
    print("📚 Bienvenido a Alejandría 🏛️")
    library = LibraryService()

    # Ejemplo de flujo básico
    user = library.register_user("Maria")
    book = library.upload_book("Frankenstein", "Mary Shelley")

    print(library.borrow_book("Maria", "Frankenstein"))
    print(library.review_book("Maria", "Frankenstein", "Me encantó la historia.", 5))
    print(f"Puntuación media: {book.average_rating()}")
    print(library.return_book("Maria", "Frankenstein"))

if __name__ == "__main__":
    main()
