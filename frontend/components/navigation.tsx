"use client"

import { useRouter, usePathname } from "next/navigation"
import { Activity, ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function Navigation() {
  const router = useRouter()
  const pathname = usePathname()

  const pages = ["/safety", "/home", "/remote"]
  const currentIndex = pages.indexOf(pathname)

  const navigatePrevious = () => {
    if (currentIndex > 0) {
      router.push(pages[currentIndex - 1])
    } else {
      // Wrap around to the last page
      router.push(pages[pages.length - 1])
    }
  }

  const navigateNext = () => {
    if (currentIndex < pages.length - 1) {
      router.push(pages[currentIndex + 1])
    } else {
      // Wrap around to the first page
      router.push(pages[0])
    }
  }

  const getModeName = (path: string) => {
    switch (path) {
      case "/safety":
        return "Safety Control"
      case "/home":
        return "Patrol Mode"
      case "/remote":
        return "Remote Control"
      default:
        return "System Control"
    }
  }

  return (
    <div className="flex items-center justify-between w-full px-4 py-3 bg-[#0a1520] bg-opacity-90 backdrop-blur-md border-b border-[#50bedc]/30">
      <div className="flex items-center">
        <Activity className="h-4 w-4 mr-2 text-[#50bedc]" />
        <span className="text-sm text-[#50bedc]">SYSTEM ACTIVE</span>
      </div>

      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          onClick={navigatePrevious}
          className="bg-transparent border-[#50bedc]/30 text-[#50bedc] rounded-full p-1 h-8 w-8 flex items-center justify-center"
        >
          <ChevronLeft className="h-5 w-5" />
        </Button>

        <div className="text-xl font-bold text-[#50bedc] glow-text">{getModeName(pathname)}</div>

        <Button
          variant="outline"
          onClick={navigateNext}
          className="bg-transparent border-[#50bedc]/30 text-[#50bedc] rounded-full p-1 h-8 w-8 flex items-center justify-center"
        >
          <ChevronRight className="h-5 w-5" />
        </Button>
      </div>

      <div className="flex items-center">
        <span className="text-sm text-[#50bedc]">MaoMao Security Bot</span>
      </div>
    </div>
  )
}
