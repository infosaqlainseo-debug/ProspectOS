with open("backend/tests/test_pipeline.py", "r") as f:
    content = f.read()

content = content.replace("        for c in companies:\n            if c.company_name.startswith(\"Company A\") or c.company_name.startswith(\"Company B\") or c.company_name.startswith(\"No Website\"):\n                await db_session.delete(c)", """
        # Cleanup properly
        from app.models import Discovery
        for c in companies:
            if c.company_name.startswith("Company A") or c.company_name.startswith("Company B") or c.company_name.startswith("No Website"):
                discs = (await db_session.execute(select(Discovery).where(Discovery.company_id == c.id))).scalars().all()
                for d in discs:
                    await db_session.delete(d)
                doms = (await db_session.execute(select(Domain).where(Domain.company_id == c.id))).scalars().all()
                for dom in doms:
                    await db_session.delete(dom)
                await db_session.delete(c)
""")

with open("backend/tests/test_pipeline.py", "w") as f:
    f.write(content)
