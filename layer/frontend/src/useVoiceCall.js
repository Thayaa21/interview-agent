import { useCallback, useEffect, useRef, useState } from "react";
import { startCall, sendAnswer } from "./api.js";

// Browser voice-call hook. Drives the conversation loop entirely in the
// browser using the Web Speech API:
//   agent speaks (speechSynthesis) -> we listen (SpeechRecognition) ->
//   send the transcript to the backend -> speak the next agent line -> repeat.
//
// Chrome/Edge only (SpeechRecognition support). Falls back gracefully with a
// clear status if unsupported.

const SpeechRecognition =
  typeof window !== "undefined" &&
  (window.SpeechRecognition || window.webkitSpeechRecognition);

export function isVoiceSupported() {
  return Boolean(SpeechRecognition) && typeof window !== "undefined" && "speechSynthesis" in window;
}

export function useVoiceCall({ onSessionId } = {}) {
  const [status, setStatus] = useState("idle"); // idle|speaking|listening|thinking|done|error
  const [sessionId, setSessionId] = useState(null);
  const [partial, setPartial] = useState("");
  const [error, setError] = useState("");

  const recogRef = useRef(null);
  const sessionRef = useRef(null);
  const finishedRef = useRef(false);

  // --- text to speech -----------------------------------------------------
  const speak = useCallback((text) => {
    return new Promise((resolve) => {
      if (!text) return resolve();
      const u = new SpeechSynthesisUtterance(text);
      u.rate = 1.0;
      u.onend = () => resolve();
      u.onerror = () => resolve();
      setStatus("speaking");
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
    });
  }, []);

  // --- one round of listening (resolves with the final transcript) --------
  const listenOnce = useCallback(() => {
    return new Promise((resolve) => {
      const recog = new SpeechRecognition();
      recogRef.current = recog;
      recog.lang = "en-US";
      recog.interimResults = true;
      recog.continuous = false;
      recog.maxAlternatives = 1;

      let finalText = "";
      recog.onresult = (e) => {
        let interim = "";
        for (let i = e.resultIndex; i < e.results.length; i++) {
          const r = e.results[i];
          if (r.isFinal) finalText += r[0].transcript;
          else interim += r[0].transcript;
        }
        setPartial(finalText || interim);
      };
      recog.onerror = (e) => {
        // no-speech / aborted are common; just resolve with whatever we have
        resolve(finalText.trim());
      };
      recog.onend = () => {
        setPartial("");
        resolve(finalText.trim());
      };
      setStatus("listening");
      try {
        recog.start();
      } catch (_) {
        resolve("");
      }
    });
  }, []);

  // --- the conversation loop ----------------------------------------------
  const runLoop = useCallback(async () => {
    while (!finishedRef.current) {
      const answer = await listenOnce();
      if (finishedRef.current) break;
      if (!answer) {
        // Nothing heard — prompt to repeat and listen again.
        await speak("Sorry, I didn't catch that. Could you say it again?");
        continue;
      }
      setStatus("thinking");
      const resp = await sendAnswer(sessionRef.current, answer);
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
    try {
      recogRef.current && recogRef.current.abort();
    } catch (_) {}
    window.speechSynthesis && window.speechSynthesis.cancel();
    setStatus("done");
  }, []);

  useEffect(() => () => stop(), [stop]);

  return { status, sessionId, partial, error, start, stop, supported: isVoiceSupported() };
}
