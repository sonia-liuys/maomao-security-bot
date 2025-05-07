"use client"

import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { useEffect } from "react"

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to safety mode by default
    router.push("/safety")
  }, [router])

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-black text-white">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-8 text-cyan-400">Robot Interface</h1>
        <div className="grid grid-cols-1 gap-4 w-full max-w-md">
          <Button
            onClick={() => router.push("/safety")}
            className="bg-cyan-900 hover:bg-cyan-800 text-white p-6 text-xl"
          >
            Safety Mode
          </Button>
          <Button
            onClick={() => router.push("/home")}
            className="bg-indigo-900 hover:bg-indigo-800 text-white p-6 text-xl"
          >
            Patrol Mode
          </Button>
          <Button
            onClick={() => router.push("/remote")}
            className="bg-purple-900 hover:bg-purple-800 text-white p-6 text-xl"
          >
            Remote Mode
          </Button>
        </div>
      </div>
    </main>
  )
}
