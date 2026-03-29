export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#F0F7FF] px-4 py-12 font-sans">
      {children}
    </main>
  );
}
