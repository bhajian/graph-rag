import { NextResponse } from "next/server";

const BACKEND_API_BASE_URL =
  process.env.BACKEND_API_BASE_URL || "http://localhost:8000";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const response = await fetch(`${BACKEND_API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const text = await response.text();
    const contentType = response.headers.get("content-type") || "application/json";

    return new NextResponse(text, {
      status: response.status,
      headers: {
        "content-type": contentType,
      },
    });
  } catch (error) {
    console.error("Failed to forward chat request:", error);
    return NextResponse.json(
      { message: "Unable to reach backend chat service" },
      { status: 502 },
    );
  }
}
