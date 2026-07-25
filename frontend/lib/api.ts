import type { ChatAction, Message, Profile } from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "";

export async function getProfile(signal?: AbortSignal): Promise<Profile> {
  const response = await fetch(`${API_URL}/api/profile`, { signal });
  if (!response.ok) throw new Error("Could not load the portfolio profile.");
  return response.json();
}

export async function sendChat(
  sessionId: string,
  messages: Message[],
  signal?: AbortSignal,
): Promise<{ answer: string; action: ChatAction | null }> {
  const response = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal,
    body: JSON.stringify({
      session_id: sessionId,
      conversation: messages.map(({ role, content }) => ({ role, content })),
    }),
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail ?? "MoonGPT could not complete that request.");
  }
  return payload;
}
