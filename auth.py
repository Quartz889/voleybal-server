from fastapi import HTTPException, status

def begin(path):
    users = []
    try:
        with open(path, "r") as file:
            for line in file:
                # Split by space and strip newlines
                parts = line.strip().split(" ")
                if len(parts) >= 2:
                    users.append([parts[0], parts[1]]) # [role, key]
    except FileNotFoundError:
        pass
    return users

def authSuper(users, user_key: str):
    for person in users:
        # Check for EXACT match of key and the correct role
        if person[1] == user_key and person[0] == "super":
            return True
    # Only return False after checking the WHOLE list
    return False

def authRoot(users, user_key: str):
    for person in users:
        # Check for EXACT match of key and the correct role
        if person[1] == user_key and person[0] == "root":
            return True
    return False

def exceptionUnauthorised():
    # Note: Keep the detail professional for standard API practices
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Unauthorized access", 
        headers={"WWW-Authenticate": "Bearer"}
    )