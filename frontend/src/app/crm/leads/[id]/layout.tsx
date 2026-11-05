export function generateStaticParams() {
  return [{ id: "preview" }];
}

export default function LeadDetailLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
