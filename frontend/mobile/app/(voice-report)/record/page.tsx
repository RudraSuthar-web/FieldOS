"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Quote, Sparkles } from "lucide-react";
import { Button, Card, CardContent, InlineAlert, voiceApi } from "@fieldos/shared";
import type { Language } from "@fieldos/shared";
import { MobileFrame } from "../../../components/layout/MobileFrame";
import { VoiceRecorder } from "../../../components/voice/VoiceRecorder";
import { LanguageSelector } from "../../../components/voice/LanguageSelector";

const SAMPLE_SCENARIOS = [
  {
    lang: "gujarati" as Language,
    label: "Gujarati — Overheating",
    text: "Machine number 12 ma motor overheating thay chhe, vibration pan vadhi gayu chhe.",
  },
  {
    lang: "hindi" as Language,
    label: "Hindi — Vibration & Heat",
    text: "मशीन नंबर 12 में मोटर ओवरहीट हो रही है और वाइब्रेशन बढ़ गया है।",
  },
  {
    lang: "hinglish" as Language,
    label: "Hinglish — Inspection",
    text: "Machine number 12 me motor overheating ho rahi hai, vibration check karna hai.",
  },
  {
    lang: "english" as Language,
    label: "English — Motor Anomaly",
    text: "Machine number 12 motor is overheating and vibration has significantly increased.",
  },
];

export default function RecordPage() {
  const router = useRouter();
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcription, setTranscription] = useState("");
  const [language, setLanguage] = useState<Language>("english");
  const [extracted, setExtracted] = useState<any>(null);
  const [error, setError] = useState("");

  const handleRecorded = useCallback(
    async (blob: Blob) => {
      setError("");
      setTranscription("");
      setExtracted(null);
      setIsProcessing(true);
      try {
        const result = await voiceApi.transcribe(blob, language);
        setTranscription(result.transcription);
        setExtracted(result.extracted);
        // Persist for the confirm page
        sessionStorage.setItem("fieldos_voice_result", JSON.stringify(result));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Transcription failed. Please try again.");
      } finally {
        setIsProcessing(false);
      }
    },
    [language]
  );

  const handleUseScenario = useCallback(
    async (text: string, lang: Language) => {
      setLanguage(lang);
      setError("");
      setTranscription("");
      setExtracted(null);
      setIsProcessing(true);
      try {
        const result = await voiceApi.transcribe(text, lang);
        setTranscription(result.transcription);
        setExtracted(result.extracted);
        sessionStorage.setItem("fieldos_voice_result", JSON.stringify(result));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Processing failed. Please try again.");
      } finally {
        setIsProcessing(false);
      }
    },
    []
  );

  const ready = !isProcessing && !!transcription && !!extracted;

  return (
    <MobileFrame
      back="/"
      requireAuth
      footer={
        ready ? (
          <Button size="lg" className="w-full" onClick={() => router.push("/confirm")}>
            Review details <ArrowRight className="h-5 w-5" />
          </Button>
        ) : undefined
      }
    >
      <h1 className="text-2xl font-bold tracking-tight">Report an issue</h1>
      <p className="mt-1 text-sm text-muted-foreground">Speak in your language. We’ll write it up for you.</p>

      <section aria-labelledby="lang-label" className="mt-5">
        <p id="lang-label" className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Language
        </p>
        <LanguageSelector value={language} onChange={setLanguage} disabled={isProcessing} />
      </section>

      <VoiceRecorder className="mt-6" onComplete={handleRecorded} isProcessing={isProcessing} />

      <div className="mt-4 rounded-lg border border-dashed border-border bg-surface/50 p-3">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          <Sparkles className="h-3.5 w-3.5 text-primary" />
          <span>Or test with a sample voice report</span>
        </div>
        <div className="mt-2.5 grid grid-cols-1 gap-1.5 sm:grid-cols-2">
          {SAMPLE_SCENARIOS.map((s) => (
            <button
              key={s.label}
              type="button"
              disabled={isProcessing}
              onClick={() => handleUseScenario(s.text, s.lang)}
              className="flex flex-col items-start rounded-md border border-border/60 bg-background/80 p-2 text-left text-xs transition-colors hover:bg-accent hover:border-primary/50 disabled:opacity-50"
            >
              <span className="font-semibold text-foreground">{s.label}</span>
              <span className="mt-0.5 line-clamp-1 text-muted-foreground">{s.text}</span>
            </button>
          ))}
        </div>
      </div>

      {error && (
        <InlineAlert variant="danger" className="mt-4">
          {error}
        </InlineAlert>
      )}

      {transcription && (
        <Card className="mt-6 animate-slide-up">
          <CardContent className="pt-4 sm:pt-5">
            <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              <Quote className="h-3.5 w-3.5" aria-hidden="true" /> What we heard
            </div>
            <p className="mt-2 break-words text-base leading-relaxed">{transcription}</p>
          </CardContent>
        </Card>
      )}

      {extracted && (
        <Card className="mt-3 animate-slide-up">
          <CardContent className="pt-4 sm:pt-5">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Quick summary</p>
            <dl className="mt-2 grid grid-cols-[auto,1fr] gap-x-4 gap-y-1.5 text-sm">
              <dt className="text-muted-foreground">Equipment</dt>
              <dd className="font-medium">{extracted.equipment_name || "—"}</dd>
              <dt className="text-muted-foreground">Issue</dt>
              <dd className="font-medium">{extracted.issue || "—"}</dd>
              <dt className="text-muted-foreground">Category</dt>
              <dd className="font-medium">{extracted.category || "—"}</dd>
              <dt className="text-muted-foreground">Severity</dt>
              <dd className="font-medium">{extracted.severity || "—"}</dd>
            </dl>
          </CardContent>
        </Card>
      )}
    </MobileFrame>
  );
}
