export function generateStaticParams() {
  return [{ id: "preview" }];
}

export default function CompanyDetailLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
