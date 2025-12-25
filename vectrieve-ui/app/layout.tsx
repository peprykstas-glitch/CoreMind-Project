import type { Metadata } from "next";
import { Inter } from "next/font/google"; // 👈 Оцей рядок виправляє помилку 'inter'
import "./globals.css"; // 👈 Оцей рядок підключає стилі (щоб було красиво)

// Ініціалізуємо шрифт
const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Vectrieve AI",
  description: "Next Gen Knowledge Base",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className} suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}