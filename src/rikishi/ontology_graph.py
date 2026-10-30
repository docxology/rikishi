from collections.abc import Iterator


def strong_components(parents: dict[str, set[str]], children: dict[str, set[str]]) -> list[list[str]]:
    """Iterative Kosaraju traversal avoids recursion limits on long source chains."""
    visited: set[str] = set()
    finished: list[str] = []
    for start in sorted(parents):
        if start in visited:
            continue
        visited.add(start)
        stack: list[tuple[str, Iterator[str]]] = [(start, iter(sorted(parents[start])))]
        while stack:
            name, neighbors = stack[-1]
            neighbor = next(neighbors, None)
            if neighbor is None:
                finished.append(name)
                stack.pop()
            elif neighbor not in visited:
                visited.add(neighbor)
                stack.append((neighbor, iter(sorted(parents[neighbor]))))
    assigned: set[str] = set()
    components = []
    for start in reversed(finished):
        if start in assigned:
            continue
        pending = [start]
        assigned.add(start)
        members = []
        while pending:
            name = pending.pop()
            members.append(name)
            for neighbor in children[name] - assigned:
                assigned.add(neighbor)
                pending.append(neighbor)
        components.append(sorted(members))
    return sorted(components)


def weak_components(parents: dict[str, set[str]], children: dict[str, set[str]]) -> dict[str, str]:
    assignments: dict[str, str] = {}
    for start in sorted(parents):
        if start in assignments:
            continue
        assignments[start] = start
        pending = [start]
        while pending:
            name = pending.pop()
            for neighbor in parents[name] | children[name]:
                if neighbor not in assignments:
                    assignments[neighbor] = start
                    pending.append(neighbor)
    return assignments
