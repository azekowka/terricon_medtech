"use client";

import { useState } from "react";
import { Stethoscope } from "lucide-react";
import { doctorAvatar } from "@/lib/format";

export function DoctorAvatar({
  src,
  name,
  className = "",
  iconSize = 24,
}: {
  src?: string | null;
  name?: string;
  className?: string;
  iconSize?: number;
}) {
  const url = doctorAvatar(src);
  const [err, setErr] = useState(false);
  return (
    <div className={`overflow-hidden bg-slate-100 ${className}`}>
      {url && !err ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={url}
          alt={name || "doctor"}
          className="h-full w-full object-cover"
          loading="lazy"
          referrerPolicy="no-referrer"
          onError={() => setErr(true)}
        />
      ) : (
        <div className="flex h-full w-full items-center justify-center text-slate-300">
          <Stethoscope size={iconSize} />
        </div>
      )}
    </div>
  );
}
