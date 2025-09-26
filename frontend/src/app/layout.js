import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Med-Bot - Your Medical Assistant',
  description: 'RAG-powered medical assistant to help you find the right doctors and medical information.',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-cyan-50">
          {children}
        </div>
      </body>
    </html>
  )
}