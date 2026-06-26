import "./globals.css";
import { Plus_Jakarta_Sans } from "next/font/google";
import { Providers } from "./providers";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta",
});

export const metadata = {
  metadataBase: new URL("https://aurarecruiting.com"),
  title: "AuraRecruiting — AI-Powered Hiring Platform",
  description: "Score resumes, rank candidates, and hire faster with AI.",
  openGraph: {
    title: "AuraRecruiting",
    description: "AI-Powered Hiring Platform for modern teams.",
    url: "https://aurarecruiting.com",
    siteName: "AuraRecruiting",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
      },
    ],
    locale: "en_US",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={jakarta.variable}>
      <body className={jakarta.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
