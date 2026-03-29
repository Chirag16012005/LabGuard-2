import Link from "next/link";
import { ShieldCheck, FileText, Search, Users, Activity, BookOpen, GraduationCap } from "lucide-react";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-[#F0F7FF] text-slate-800 font-sans">
      {/* Navbar area */}
      <header className="flex h-16 items-center justify-between border-b border-blue-100 bg-white px-4 sm:px-8 shadow-sm">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-blue-100 bg-[#F0F7FF]">
            <ShieldCheck className="h-5 w-5 text-blue-600" strokeWidth={1.5} />
          </div>
          <span className="font-semibold tracking-tight text-slate-800">LabGuard</span>
        </div>
        <div className="flex items-center gap-4 text-sm font-medium">
          <Link href="/login" className="text-slate-600 transition-colors hover:text-blue-600">
            Login
          </Link>
          <Link
            href="/register"
            className="rounded-lg border-none bg-blue-500 px-4 py-2 text-white transition-all hover:translate-y-[-1px] hover:bg-blue-600 hover:shadow-sm"
          >
            Get Started
          </Link>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="flex flex-col items-center justify-center px-4 py-24 text-center sm:px-8 sm:py-32">
          <div className="w-full max-w-3xl space-y-6">
            <h1 className="text-4xl font-semibold tracking-tight text-slate-800 sm:text-5xl md:text-6xl text-balance">
              AI-powered Plagiarism Detection for Classrooms
            </h1>
            <p className="mx-auto max-w-2xl text-lg text-slate-600 sm:text-xl text-balance">
              Ensure academic integrity with lightning-fast similarity checks, classroom comparisons, and actionable highlighted reports.
            </p>
            <div className="pt-4 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                href="/register"
                className="flex w-full sm:w-auto items-center justify-center rounded-xl border-none bg-blue-500 px-8 py-3.5 text-base font-medium text-white transition-all hover:translate-y-[-1px] hover:bg-blue-600 hover:shadow-sm"
              >
                Get Started
              </Link>
              <Link
                href="/login"
                className="flex w-full sm:w-auto items-center justify-center rounded-xl border border-blue-100 bg-white px-8 py-3.5 text-base font-medium text-slate-700 transition-all hover:translate-y-[-1px] hover:bg-[#F0F7FF] hover:border-blue-200"
              >
                Login
              </Link>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="mx-auto w-full max-w-6xl px-4 py-20 sm:px-8">
          <div className="mb-12">
            <h2 className="text-2xl font-semibold tracking-tight text-slate-800">Powerful Features</h2>
            <p className="mt-2 text-slate-600">Everything you need to maintain academic standards.</p>
          </div>
          
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <div className="flex flex-col rounded-xl border border-blue-50 bg-white p-6 transition-transform hover:translate-y-[-2px] hover:border-blue-100 hover:shadow-sm shadow-sm">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg border border-blue-100 bg-[#F0F7FF]">
                <FileText className="h-5 w-5 text-blue-600" strokeWidth={1.5} />
              </div>
              <h3 className="text-lg font-semibold text-slate-800">Upload Documents</h3>
              <p className="mt-2 text-slate-600 leading-relaxed font-sans text-sm">
                Support for PDFs, Word files, and plain text. Upload single files or bulk batches.
              </p>
            </div>

            <div className="flex flex-col rounded-xl border border-blue-50 bg-white p-6 transition-transform hover:translate-y-[-2px] hover:border-blue-100 hover:shadow-sm shadow-sm">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg border border-blue-100 bg-[#F0F7FF]">
                <Search className="h-5 w-5 text-blue-600" strokeWidth={1.5} />
              </div>
              <h3 className="text-lg font-semibold text-slate-800">Similarity Detection</h3>
              <p className="mt-2 text-slate-600 leading-relaxed font-sans text-sm">
                Advanced AI algorithms scan across millions of sources to identify potential matches.
              </p>
            </div>

            <div className="flex flex-col rounded-xl border border-blue-50 bg-white p-6 transition-transform hover:translate-y-[-2px] hover:border-blue-100 hover:shadow-sm shadow-sm">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg border border-blue-100 bg-[#F0F7FF]">
                <Users className="h-5 w-5 text-blue-600" strokeWidth={1.5} />
              </div>
              <h3 className="text-lg font-semibold text-slate-800">Classroom Comparison</h3>
              <p className="mt-2 text-slate-600 leading-relaxed font-sans text-sm">
                Cross-reference student submissions within the same classroom to detect peer copying.
              </p>
            </div>

            <div className="flex flex-col rounded-xl border border-blue-50 bg-white p-6 transition-transform hover:translate-y-[-2px] hover:border-blue-100 hover:shadow-sm shadow-sm">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg border border-blue-100 bg-[#F0F7FF]">
                <Activity className="h-5 w-5 text-blue-600" strokeWidth={1.5} />
              </div>
              <h3 className="text-lg font-semibold text-slate-800">Highlighted Reports</h3>
              <p className="mt-2 text-slate-600 leading-relaxed font-sans text-sm">
                Clear, annotated reports pinpointing the exact text matches and their original sources.
              </p>
            </div>
          </div>
        </section>

        {/* Role-based Section */}
        <section className="mx-auto w-full max-w-6xl px-4 py-20 sm:px-8">
          <div className="mb-12">
            <h2 className="text-2xl font-semibold tracking-tight text-slate-800">Built for Everyone</h2>
            <p className="mt-2 text-slate-600">Tailored experiences depending on your role.</p>
          </div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
            {/* Student Role */}
            <div className="group rounded-xl border border-blue-50 bg-white p-8 transition-transform hover:translate-y-[-2px] hover:border-blue-100 shadow-sm">
              <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl border border-blue-100 bg-blue-50">
                <BookOpen className="h-6 w-6 text-blue-600" strokeWidth={1.5} />
              </div>
              <h3 className="mb-4 text-xl font-semibold text-slate-800 flex items-center gap-2">
                For Students
              </h3>
              <ul className="space-y-4 text-slate-500 font-sans text-sm">
                <li className="flex items-start gap-3">
                  <div className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-300" />
                  <p>Upload drafts to check similarity before final submission.</p>
                </li>
                <li className="flex items-start gap-3">
                  <div className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-300" />
                  <p>Review highlighted reports to improve citing and referencing.</p>
                </li>
                <li className="flex items-start gap-3">
                  <div className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-300" />
                  <p>A simple, focused dashboard outlining past submissions.</p>
                </li>
              </ul>
            </div>

            {/* Teacher Role */}
            <div className="group rounded-xl border border-blue-50 bg-white p-8 transition-transform hover:translate-y-[-2px] hover:border-blue-100 shadow-sm">
              <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl border border-blue-100 bg-blue-50">
                <GraduationCap className="h-6 w-6 text-blue-600" strokeWidth={1.5} />
              </div>
              <h3 className="mb-4 text-xl font-semibold text-slate-800 flex items-center gap-2">
                For Teachers
              </h3>
              <ul className="space-y-4 text-slate-500 font-sans text-sm">
                <li className="flex items-start gap-3">
                  <div className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-300" />
                  <p>Seamlessly manage multiple classrooms and assignments.</p>
                </li>
                <li className="flex items-start gap-3">
                  <div className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-300" />
                  <p>Detect plagiarism across internet sources and your own students.</p>
                </li>
                <li className="flex items-start gap-3">
                  <div className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-300" />
                  <p>Export similarity reports to share feedback effectively.</p>
                </li>
              </ul>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-blue-100 bg-white mt-8">
        <div className="mx-auto flex w-full max-w-6xl flex-col items-center justify-between gap-4 px-4 py-8 sm:flex-row sm:px-8">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-blue-600" strokeWidth={1.5} />
            <span className="font-semibold text-slate-800">LabGuard</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-slate-500">
            <Link href="#" className="hover:text-blue-600 transition-colors">Privacy</Link>
            <Link href="#" className="hover:text-blue-600 transition-colors">Terms</Link>
            <Link href="#" className="hover:text-blue-600 transition-colors">Support</Link>
          </div>
          <p className="text-sm text-slate-500">
            © {new Date().getFullYear()} LabGuard. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
