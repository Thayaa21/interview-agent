import { useCallback, useRef as _useRef, useState, useEffect } from "react";
import { Room, RoomEvent, Track } from "livekit-client";

// Connects the browser to the REAL LiveKit agent:
//   - fetches a join token (encodes the chosen role in the room name),
//   - joins the room, publishes the mic, plays the agent's audio,
//   - decodes the agent's data messages (topic "interview") into events
//     (session_start | turn | guardrail | analysis | session_end) that the
//     dashboard panels render live.
//
// The agent worker must be running in auto-dispatch mode:
//   AGENT_AUTO_DISPATCH=1 python -m src.agent dev

const decoder = new TextDecoder();

export function useLiveCall({ onEvent } = {}) {
  const [status, setStatus] = useState("idle"); // idle|connecting|connected|error|ended
  const [error, setError] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const roomRef = _useRef(null);
  const audioElRef = _useRef(null);

  const connect = useCallback(
    async (role) => {
      setError("");
      setStatus("connecting");
      try {
        let r;
        try {
          r = await fetch(`/token?role=${encodeURIComponent(role)}`);
        } catch (netErr) {
          throw new Error("Can't reach the token server. Start it: python -m src.token_server (port 8790).");
        }
        const ctype = r.headers.get("content-type") || "";
        if (!r.ok || !ctype.includes("application/json")) {
          throw new Error(
            `Token server returned a non-JSON response (status ${r.status}). ` +
              "Is 'python -m src.token_server' running on port 8790, and are your LiveKit keys set in .env?"
          );
        }
        const { url, token, room: roomName } = await r.json();
        if (!url || !token) throw new Error("Token server response missing url/token — check LiveKit keys in .env.");
        setSessionId(roomName);

        const room = new Room({ adaptiveStream: true, dynacast: true });
        roomRef.current = room;

        // Agent audio -> attach to a hidden container so it plays.
        room.on(RoomEvent.TrackSubscribed, (track) => {
          if (track.kind === Track.Kind.Audio) {
            const el = track.attach();
            el.autoplay = true;
            if (audioElRef.current) audioElRef.current.appendChild(el);
            else document.body.appendChild(el);
          }
        });

        // All dashboard events (turn / guardrail / analysis / session_*) come
        // as data messages on the "interview" topic from the agent. This is the
        // reliable path (guardrails already worked this way).
        room.on(RoomEvent.DataReceived, (payload, _participant, _kind, topic) => {
          if (topic && topic !== "interview") return;
          try {
            const ev = JSON.parse(decoder.decode(payload));
            onEvent && onEvent(ev);
          } catch (_) {}
        });

        room.on(RoomEvent.Disconnected, () => setStatus("ended"));

        await room.connect(url, token);
        await room.localParticipant.setMicrophoneEnabled(true);
        setStatus("connected");
      } catch (e) {
        setError(String(e && e.message ? e.message : e));
        setStatus("error");
      }
    },
    [onEvent]
  );

  const disconnect = useCallback(() => {
    try {
      roomRef.current && roomRef.current.disconnect();
    } catch (_) {}
    setStatus("ended");
  }, []);

  useEffect(() => () => disconnect(), [disconnect]);

  return { status, error, sessionId, connect, disconnect, audioElRef };
}
