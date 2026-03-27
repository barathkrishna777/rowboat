"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { friends as friendsApi, User } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function FriendsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [friendsList, setFriendsList] = useState<User[]>([]);
  const [incoming, setIncoming] = useState<{ id: number; requester?: { name: string; email: string } }[]>([]);
  const [addValue, setAddValue] = useState("");
  const [addError, setAddError] = useState("");
  const [addSuccess, setAddSuccess] = useState("");

  const refresh = async () => {
    if (!user) return;
    try {
      const [f, i] = await Promise.all([
        friendsApi.list(user.id),
        friendsApi.incoming(user.id) as Promise<{ id: number; requester?: { name: string; email: string } }[]>,
      ]);
      setFriendsList(f);
      setIncoming(i);
    } catch { /* ignore */ }
  };

  useEffect(() => {
    if (!loading && !user) { router.replace("/login"); return; }
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !addValue) return;
    setAddError(""); setAddSuccess("");
    try {
      const isEmail = addValue.includes("@");
      await friendsApi.sendRequest(user.id, isEmail ? { to_email: addValue } : { to_username: addValue });
      setAddSuccess(`Request sent to ${addValue}`);
      setAddValue("");
    } catch (err: unknown) {
      setAddError(err instanceof Error ? err.message : "Failed");
    }
  };

  const handleRespond = async (fid: number, accept: boolean) => {
    if (!user) return;
    await friendsApi.respond(user.id, fid, accept);
    refresh();
  };

  const handleRemove = async (friendId: string) => {
    if (!user) return;
    await friendsApi.remove(user.id, friendId);
    refresh();
  };

  if (loading || !user) return <p className="text-center mt-20">Loading...</p>;

  return (
    <div className="max-w-md mx-auto">
      <h1 className="text-2xl font-bold mb-6">Friends</h1>

      {/* Add friend */}
      <form onSubmit={handleAdd} className="flex gap-2 mb-6">
        <input
          value={addValue} onChange={(e) => setAddValue(e.target.value)}
          placeholder="Email or username"
          className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-orange-500"
        />
        <button type="submit" className="bg-orange-500 text-white rounded-lg px-4 py-2 font-semibold hover:bg-orange-600">
          Add
        </button>
      </form>
      {addError && <p className="text-red-500 text-sm mb-4">{addError}</p>}
      {addSuccess && <p className="text-green-600 text-sm mb-4">{addSuccess}</p>}

      {/* Incoming requests */}
      {incoming.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-2">Pending Requests</h2>
          {incoming.map((req) => (
            <div key={req.id} className="flex items-center justify-between bg-orange-50 border border-orange-200 rounded-lg p-3 mb-2">
              <span className="font-medium">{req.requester?.name || "Unknown"}</span>
              <div className="flex gap-2">
                <button onClick={() => handleRespond(req.id, true)} className="text-green-600 font-semibold text-sm">Accept</button>
                <button onClick={() => handleRespond(req.id, false)} className="text-red-500 font-semibold text-sm">Decline</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Friends list */}
      {friendsList.length > 0 ? (
        friendsList.map((f) => (
          <div key={f.id} className="flex items-center justify-between bg-white border border-gray-200 rounded-lg p-3 mb-2">
            <div>
              <div className="font-medium">{f.name}</div>
              <div className="text-sm text-gray-500">{f.email}</div>
            </div>
            <button onClick={() => handleRemove(f.id)} className="text-red-400 text-sm hover:text-red-600">Remove</button>
          </div>
        ))
      ) : (
        <p className="text-gray-400 text-center mt-8">No friends yet. Add someone above!</p>
      )}
    </div>
  );
}
