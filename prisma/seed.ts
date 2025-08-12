import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  const count = await prisma.run.count();
  if (count > 0) return;
  await prisma.run.createMany({
    data: [
      { title: 'Initial analysis', status: 'success', finishedAt: new Date() },
      { title: 'Crawl market gaps', status: 'running' },
      { title: 'Draft report', status: 'queued' },
    ],
  });
}

main().finally(async () => {
  await prisma.$disconnect();
});
