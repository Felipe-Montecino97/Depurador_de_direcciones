from cleaner import clean_address
from scorer import score_address
from deduplicator import find_duplicates


def main():
    example_addresses = [
        "Av. Providencia 1234, Depto 501, Santiago",
        "Avenida Providencia #1234 departamento 501 Santiago",
        "asdf qwer zxcv 999",
        "Los Leones 220, Providencia",
        "Apoquindo 4501 torre b oficina 1203 las condes",
        "calle falsa sin numero prueba",
    ]

    cleaned_addresses = []

    print("RESULTADOS DE LIMPIEZA Y SCORING")
    print("=" * 50)

    for address in example_addresses:
        cleaned = clean_address(address)
        score = score_address(cleaned)

        cleaned_addresses.append(cleaned)

        print("Original:", address)
        print("Limpia:", cleaned)
        print("Score:", score["score"])
        print("Estado:", score["status"])
        print("Razones:")
        for reason in score["reasons"]:
            print("-", reason)
        print("-" * 50)

    print("\nGRUPOS DE DUPLICADOS")
    print("=" * 50)

    duplicate_groups = find_duplicates(cleaned_addresses, threshold=88)

    for group in duplicate_groups:
        print("Principal:", group["main_address"])
        print("Cantidad en grupo:", group["count"])
        print("Direcciones:")
        for item in group["duplicates"]:
            print("-", item)
        print("-" * 50)


if __name__ == "__main__":
    main()
