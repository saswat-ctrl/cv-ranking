import { Metadata } from "next";

export const metadata: Metadata = {
    title: "Sign Up - HR CV Shortlisting",
    description: "Create a new account",
};

export default function SignupLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
