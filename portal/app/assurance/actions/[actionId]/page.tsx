import { AssuranceActionPage } from "@/components/assurance/AssuranceActionPage";
import {
  getAllAssuranceActionIds,
  getAssuranceActionById,
} from "@/lib/assuranceData";

export async function generateStaticParams() {
  const ids = await getAllAssuranceActionIds();
  return ids.map((actionId) => ({ actionId }));
}

export const dynamicParams = process.env.NODE_ENV === "development";

export default async function AssuranceActionRoute({
  params,
}: {
  params: Promise<{ actionId: string }>;
}) {
  const { actionId } = await params;
  const model = await getAssuranceActionById(actionId);

  if (!model) {
    return (
      <main className="mx-auto max-w-5xl p-8">
        <h1 className="text-3xl font-semibold">Action not found</h1>
        <p className="mt-2 text-gray-600">
          No assurance action with id “{actionId}”. Run{" "}
          <code className="rounded bg-gray-100 px-1">
            sm export-assurance-portal-data
          </code>
          .
        </p>
      </main>
    );
  }

  return <AssuranceActionPage model={model} />;
}
