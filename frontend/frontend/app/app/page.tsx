"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AppIndex() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/app/chat/new");
  }, [router]);
  return null;
}
