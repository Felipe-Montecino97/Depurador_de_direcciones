from rapidfuzz import fuzz


def calculate_similarity(address_a: str, address_b: str) -> float:
    return fuzz.token_sort_ratio(address_a, address_b)


def are_similar(address_a: str, address_b: str, threshold: int = 90) -> bool:
    similarity = calculate_similarity(address_a, address_b)
    return similarity >= threshold


def find_exact_duplicates(addresses: list[str]) -> list[dict]:
    groups: dict[str, list[int]] = {}
    for index, address in enumerate(addresses):
        groups.setdefault(address, []).append(index)

    return [
        {
            "address": address,
            "indexes": indexes,
            "count": len(indexes),
        }
        for address, indexes in groups.items()
        if len(indexes) > 1
    ]


def find_similar_duplicates(addresses: list[str], threshold: int = 90) -> list[dict]:
    similar_pairs = []
    for i in range(len(addresses)):
        for j in range(i + 1, len(addresses)):
            if addresses[i] == addresses[j]:
                continue

            similarity = calculate_similarity(addresses[i], addresses[j])
            if similarity >= threshold:
                similar_pairs.append(
                    {
                        "index_a": i,
                        "address_a": addresses[i],
                        "index_b": j,
                        "address_b": addresses[j],
                        "similarity": round(similarity, 2),
                    }
                )

    return similar_pairs


def find_duplicates(addresses: list[str], threshold: int = 90) -> dict:
    return {
        "exact": find_exact_duplicates(addresses),
        "similar": find_similar_duplicates(addresses, threshold=threshold),
    }
