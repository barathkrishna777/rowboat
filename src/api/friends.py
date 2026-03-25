"""Friend management API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.models.user import Friendship, FriendshipStatus, User

router = APIRouter()

# In-memory stores matching the MVP pattern used by groups/preferences
_users: dict[str, User] = {}
_friendships: dict[int, Friendship] = {}
_friendship_counter = 0


def _get_or_register_user(user_id: str, name: str = "", email: str = "") -> User:
    """Retrieve an existing user or register a new one from session data."""
    if user_id in _users:
        return _users[user_id]
    user = User(id=user_id, name=name or "Unknown", email=email or "")
    _users[user_id] = user
    return user


class RegisterUserRequest(BaseModel):
    user_id: str
    name: str
    email: str


class SendFriendRequestBody(BaseModel):
    to_email: str


class RespondFriendRequestBody(BaseModel):
    accept: bool


# ── User registration (called by UI on group creation) ────────────────


@router.post("/register", response_model=User)
async def register_user(req: RegisterUserRequest):
    """Register or update a user so they can be found by email."""
    user = User(id=req.user_id, name=req.name, email=req.email)
    _users[req.user_id] = user
    return user


@router.get("/search", response_model=list[User])
async def search_users(q: str = ""):
    """Search registered users by name or email."""
    if not q or len(q) < 2:
        return []
    q_lower = q.lower()
    return [
        u for u in _users.values()
        if q_lower in u.name.lower() or q_lower in u.email.lower()
    ]


# ── Friend requests ───────────────────────────────────────────────────


@router.post("/{user_id}/request", response_model=Friendship)
async def send_friend_request(user_id: str, body: SendFriendRequestBody):
    """Send a friend request to another user by email."""
    global _friendship_counter

    if user_id not in _users:
        raise HTTPException(status_code=404, detail="Sender not registered. Call /register first.")

    target = next((u for u in _users.values() if u.email.lower() == body.to_email.lower()), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"No user found with email {body.to_email}")
    if target.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot send a friend request to yourself")

    # Check for existing friendship in either direction
    for f in _friendships.values():
        pair = {f.requester_id, f.addressee_id}
        if pair == {user_id, target.id}:
            if f.status == FriendshipStatus.ACCEPTED:
                raise HTTPException(status_code=400, detail="Already friends")
            if f.status == FriendshipStatus.PENDING:
                raise HTTPException(status_code=400, detail="Friend request already pending")

    _friendship_counter += 1
    friendship = Friendship(
        id=_friendship_counter,
        requester_id=user_id,
        addressee_id=target.id,
        status=FriendshipStatus.PENDING,
        requester=_users.get(user_id),
        addressee=target,
    )
    _friendships[_friendship_counter] = friendship
    return friendship


@router.post("/{user_id}/respond/{friendship_id}", response_model=Friendship)
async def respond_to_request(user_id: str, friendship_id: int, body: RespondFriendRequestBody):
    """Accept or decline a friend request."""
    friendship = _friendships.get(friendship_id)
    if not friendship:
        raise HTTPException(status_code=404, detail="Friend request not found")
    if friendship.addressee_id != user_id:
        raise HTTPException(status_code=403, detail="Only the addressee can respond")
    if friendship.status != FriendshipStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request already resolved")

    friendship.status = FriendshipStatus.ACCEPTED if body.accept else FriendshipStatus.DECLINED
    friendship.requester = _users.get(friendship.requester_id)
    friendship.addressee = _users.get(friendship.addressee_id)
    return friendship


# ── Friend list & pending requests ────────────────────────────────────


@router.get("/{user_id}/friends", response_model=list[User])
async def get_friends(user_id: str):
    """Get all accepted friends for a user."""
    friends: list[User] = []
    for f in _friendships.values():
        if f.status != FriendshipStatus.ACCEPTED:
            continue
        if f.requester_id == user_id:
            friend = _users.get(f.addressee_id)
        elif f.addressee_id == user_id:
            friend = _users.get(f.requester_id)
        else:
            continue
        if friend:
            friends.append(friend)
    return friends


@router.get("/{user_id}/requests/incoming", response_model=list[Friendship])
async def get_incoming_requests(user_id: str):
    """Get pending friend requests received by user."""
    incoming = []
    for f in _friendships.values():
        if f.addressee_id == user_id and f.status == FriendshipStatus.PENDING:
            f.requester = _users.get(f.requester_id)
            incoming.append(f)
    return incoming


@router.get("/{user_id}/requests/outgoing", response_model=list[Friendship])
async def get_outgoing_requests(user_id: str):
    """Get pending friend requests sent by user."""
    outgoing = []
    for f in _friendships.values():
        if f.requester_id == user_id and f.status == FriendshipStatus.PENDING:
            f.addressee = _users.get(f.addressee_id)
            outgoing.append(f)
    return outgoing


# ── Remove friend ─────────────────────────────────────────────────────


@router.delete("/{user_id}/friends/{friend_id}")
async def remove_friend(user_id: str, friend_id: str):
    """Remove an existing friendship."""
    to_remove = None
    for fid, f in _friendships.items():
        if f.status == FriendshipStatus.ACCEPTED and {f.requester_id, f.addressee_id} == {user_id, friend_id}:
            to_remove = fid
            break
    if to_remove is None:
        raise HTTPException(status_code=404, detail="Friendship not found")
    del _friendships[to_remove]
    return {"detail": "Friend removed"}
