import { useCallback, useEffect, useRef, useState } from "react";
import { startCall, sendAnswer } from "./api.js";

// Browser voice-call hook using the Web Speech API:
//   agent speaks (speechSynthesis) -> we listen (SpeechRecognition) ->
//   send transcript -> speak next agent line -> repeat.
//
// Chrome/Edge only. Key behaviors:
//  * We NEVER listen while the agent is speaking (avoids the agent hearing
//    itself / instant empty results).
//  * If a listen round ends with NO speech detected at all, we silently
//    restart listening instead of nagging "say that again". We only re-prompt
//    after several consecutive truly-empty rounds.
//  * A better-quality system voice is chosen and the rate is softened.

const SpeechRecognition =
  typeof window !== "undefined" &&
  (window.SpeechRecognition || window.webkitSpeechRecognition);

export function isVoiceSupported() {
  return Boolean(SpeechRecognition) && typeof window !== "undefined" && "speechSynthesis" in window;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Pick the most natural available voice (browser voices vary by OS).
function pickVoice() {
  const voices = window.speechSynthesis.getVoices() || [];
  const prefer = [
    "Samantha", "Google US English", "Microsoft Aria", "Microsoft Jenny",
    "Karen", "Moira", "Google UK English Female",
  ];
  for (const name of prefer) {
    const v = voices.find((v) => v.name === name || v.name.includes(name));
    if (v) return v;
  }
  return voices.find((v) => v.lang && v.lang.startsWith("en")) || voices[0] || null;
}

export function useVoiceCall({ onSessionId } = {}) {
  const [status, setStatus] = useState("idle"); // idle|speaking|listening|thinking|done|error
  const [sessionId, setSessionId] = useState(null);
  const [partial, setPartial] = useState("");
  const [error, setError] = useState("");

  const recogRef = useRef(null);
  const sessionRef = useRef(null);
  const finishedRef = useRef(false);
  const voiceRef = useRef(null);

  useEffect(() => {
    if (!("speechSynthesis" in window)) return;
    const load = () => { voiceRef.current = pickVoice(); };
    load();
    window.speechSynthesis.onvoiceschanged = load;
  }, []);

  // --- text to speech -----------------------------------------------------
  const speak = useCallback((text) => {
    return new Promise((resolve) => {
      if (!text) return resolve();
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      if (voiceRef.current) u.voice = voiceRef.current;
      u.rate = 0.95;   // slightly slower = less robotic / clearer
      u.pitch = 1.0;
      u.onend = () => resolve();
      u.onerror = () => resolve();
      setStatus("speaking");
      window.speechSynthesis.speak(u);
    });
  }, []);

  // --- one listening round --------------------------------------------------
  // Resolves { text, heardSpeech }. heardSpeech=false means the mic detected
  // no speech at all (so we can silently retry rather than nag).
  const listenOnce = useCallback(() => {
    return new Promise((resolve) => {
      const recog = new SpeechRecognition();
      recogRef.current = recog;
      recog.lang = "en-US";
      recog.interimResults = true;
      recog.continuous = true;      // keep going through natural pauses
      recog.maxAlternatives = 1;

      let finalText = "";
      let heardSpeech = false;
      let silenceTimer = null;
      let settled = false;

      const finish = () => {
        if (settled) return;
        settled = true;
        clearTimeout(silenceTimer);
        try { recog.stop(); } catch (_) {}
        setPartial("");
        resolve({ text: finalText.trim(), heardSpeech });
      };

      // After the user has spoken, wait this long with no new words before we
      // consider the turn complete (tolerates mid-answer pauses).
      const armSilence = () => {
        clearTimeout(silenceTimer);
        silenceTimer = setTimeout(finish, 1800);
      };

      recog.onspeechstart = () => { heardSpeech = true; };
      recog.onresult = (e) => {
        heardSpeech = true;
        let interim = "";
        finalText = "";
        for (let i = 0; i < e.results.length; i++) {
          const r = e.results[i];
          if (r.isFinal) finalText += r[0].transcript + " ";
          else interim += r[0].transcript;
        }
        setPartial((finalText + interim).trim());
        armSilence();
      };
      recog.onerror = () => finish();
      recog.onend = () => finish();

      setStatus("listening");
      try {
        recog.start();
      } catch (_) {
        resolve({ text: "", heardSpeech: false });
      }
    });
  }, []);

  // --- the conversation loop ----------------------------------------------
  const runLoop = useCallback(async () => {
    let emptyRounds = 0;
    while (!finishedRef.current) {
      // Small gap so we don't capture the tail of the agent's own speech.
      await sleep(350);
      if (finishedRef.current) break;

      const { text, heardSpeech } = await listenOnce();
      if (finishedRef.current) break;

      if (!text) {
        // No usable answer. If the mic heard nothing at all, just retry
        // quietly. Only nag after 3 empty rounds in a row.
        emptyRounds += 1;
        if (!heardSpeech && emptyRounds < 3) continue;
        if (emptyRounds >= 3) {
          await speak("Take your time. When you're ready, go ahead and answer.");
          emptyRounds = 0;
        }
        continue;
      }

      emptyRounds = 0;
      setStatus("thinking");
      const resp = await sendAnswer(sessionRef.current, text);
      if (resp.agent) await speak(resp.agent);
      if (resp.finished) {
        finishedRef.current = true;
        setStatus("done");
        break;
      }
    }
  }, [listenOnce, speak]);

  const start = useCallback(
    async (candidate, role) => {
      setError("");
      if (!isVoiceSupported()) {
        setError("Voice not supported in this browser. Use Chrome or Edge.");
        setStatus("error");
        return;
      }
      finishedRef.current = false;
      setStatus("thinking");
      const resp = await startCall(candidate, role);
      if (resp.error) {
        setError(resp.error);
        setStatus("error");
        return;
      }
      sessionRef.current = resp.session_id;
      setSessionId(resp.session_id);
      onSessionId && onSessionId(resp.session_id);
      await speak(resp.agent); // greeting + first question
      runLoop();
    },
    [speak, runLoop, onSessionId]
  );

  const stop = useCallback(() => {
    finishedRef.current = true;
    try { recogRef.current && recogRef.current.abort(); } catch (_) {}
    window.speechSynthesis && window.speechSynthesis.cancel();
    setStatus("done");
  }, []);

  useEffect(() => () => stop(), [stop]);

  return { status, sessionId, partial, error, start, stop, supported: isVoiceSupported() };
}
