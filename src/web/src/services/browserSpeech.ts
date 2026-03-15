/**
 * Browser-native TTS (speechSynthesis) and STT (SpeechRecognition).
 * Free, no API key required, works entirely in the browser.
 *
 * STT UX mirrors the Whisper flow:
 *   click mic → recording state (SpeechRecognition running in background)
 *   click confirm → recognition.stop() → browser returns transcript
 *   click cancel  → recognition.abort() → discard
 */

// ── TTS ───────────────────────────────────────────────────────────────────────

export function stopBrowserTTS() {
  window.speechSynthesis.cancel();
}

export function playWithBrowserTTS(text: string): Promise<void> {
  return new Promise((resolve) => {
    stopBrowserTTS();
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = navigator.language || "zh-TW";
    utter.onend = () => resolve();
    utter.onerror = () => resolve();
    window.speechSynthesis.speak(utter);
  });
}

// ── STT ───────────────────────────────────────────────────────────────────────

export function isBrowserSTTSupported(): boolean {
  return !!(
    (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition // eslint-disable-line
  );
}

export interface BrowserSTTHandle {
  /** Stop listening and return transcript (→ transcribing state). */
  confirm: () => void;
  /** Abort without result. */
  cancel: () => void;
}

/**
 * Start a browser STT session.
 * Returns a handle with confirm/cancel, and calls back when done.
 *
 * @param onTranscript  Called with final text (empty string = nothing detected / cancelled)
 * @param onAutoEnd     Called when the browser auto-detects end-of-speech before confirm
 */
export function startBrowserSTT(
  onTranscript: (text: string) => void,
  onAutoEnd?: () => void,
): BrowserSTTHandle | null {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  if (!SR) return null;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognition = new SR() as any;
  recognition.lang = navigator.language || "zh-TW";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  recognition.continuous = true; // keep listening until user confirms

  let collected = "";
  let manuallyStopped = false;

  recognition.onresult = (e: any) => { // eslint-disable-line
    // Accumulate all results (continuous mode may fire multiple times)
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) {
        collected += (collected ? " " : "") + e.results[i][0].transcript;
      }
    }
  };

  recognition.onend = () => {
    onTranscript(collected.trim());
    if (!manuallyStopped) {
      // Browser auto-ended (e.g. long silence)
      onAutoEnd?.();
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  recognition.onerror = (e: any) => {
    if (e.error !== "aborted") onTranscript("");
  };

  recognition.start();

  return {
    confirm: () => {
      manuallyStopped = true;
      recognition.stop(); // triggers onend with collected text
    },
    cancel: () => {
      manuallyStopped = true;
      collected = "";
      recognition.abort(); // triggers onend with empty string
    },
  };
}
