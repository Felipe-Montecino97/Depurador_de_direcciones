from rapidfuzz import fuzz


def calculate_similarity(address_a: str, address_b: str) -> float:
    return fuzz.token_sort_ratio(address_a, address_b)


def are_similar(address_a: str, address_b: str, threshold: int = 90) -> bool:
    similarity = calculate_similarity(address_a, address_b)
    return similarity >= threshold


def find_duplicates(addresses: list[str], threshold: int = 90) -> list[dict]:
    results = []
    visited = set()

    for i, address in enumerate(addresses):
        if i in visited:
            continue

        group = [address]
        visited.add(i)

        for j in range(i + 1, len(addresses)):
            if j in visited:
                continue

            if are_similar(address, addresses[j], threshold):
                group.append(addresses[j])
                visited.add(j)

        results.append({
            "main_address": address,
            "duplicates": group,
            "count": len(group),
        })

    return results
