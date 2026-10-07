from workers import DurableObject, Response, WorkerEntrypoint
from urllib.parse import urlparse
from datetime import datetime, timezone
from workers import WorkerEntrypoint, Response, fetch

"""
 * Welcome to Cloudflare Workers! This is your first Durable Objects application.
 *
 * - Run `npm run dev` in your terminal to start a development server
 * - Open a browser tab at http://localhost:8787/ to see your Durable Object in action
 * - Run `npm run deploy` to publish your application
 *
 * Learn more at https://developers.cloudflare.com/durable-objects
"""

"""
 * Env provides a mechanism to reference bindings declared in wrangler.jsonc within Python
 *
 * @typedef {Object} Env
 * @property {DurableObjectNamespace} MY_DURABLE_OBJECT - The Durable Object namespace binding
"""
"""
# A Durable Object's behavior is defined in an exported Python class
class MyDurableObject(DurableObject):

     * The constructor is invoked once upon creation of the Durable Object, i.e. the first call to
     * `DurableObjectStub::get` for a given identifier (no-op constructors can be omitted)
     *
     * @param {DurableObjectState} ctx - The interface for interacting with Durable Object state
     * @param {Env} env - The interface to reference bindings declared in wrangler.jsonc

    def __init__(self, ctx, env):
        super().__init__(ctx, env)


     * The Durable Object exposes an RPC method `say_hello` which will be invoked when a Durable
     *  Object instance receives a request from a Worker via the same method invocation on the stub
     *
     * @param {string} name - The name provided to a Durable Object instance from a Worker
     * @returns {Promise<string>} The greeting to be sent back to the Worker

    async def say_hello(self, name):
        return f"Hello, {name}!"

"""

PHONE_POOLS = {
    "asb": [
    "+15612879674",
    "+15612352502",
    "+15613316657",
    "+15615447278",
    "+15618799945",
    "+15613284996",
    "+15615447458",
    "+15613313164",
    "+15614215411",
    "+15614531963",
    "+15615447456",
    "+15613284842",
    "+15613284884"
]
}

REP_PHONE = {
    "Waiting for ATT": "+15612879674",
    "Ceasars Main": "+15612352502",
    "Fred Main": "+15613316657",
    "Grant Main": "+15615447278",
    "Jason Miller": "+15618799945",
    "John Washburn": "+15613284996",
    "Matthew Ditomasso": "+15615447458",
    "Michael Cast": "+15613313164",
    "Mike Cast2": "+15614215411",
    "Noah Main": "+15614531963",
    "Sebastian Main": "+15615447456",
    "Shauna Main": "+15613284842",
    "Tals Main": "+15613284884"
}

class RoundRobin(DurableObject):
    async def next_index(self, pool_size):
        if pool_size <= 0:
            raise ValueError("Pool size must have at least one element.")

        cursor = await self.ctx.storage.get("cursor")

        if cursor is None:
            cursor = 0

        index = cursor % pool_size

        await self.ctx.storage.put("cursor", index + 1)

        return index

class Default(WorkerEntrypoint):
    """
    * This is the standard fetch handler for a Cloudflare Worker
    *
    * @param {Request} request - The request submitted to the Worker from the client
    * @param {Env} env - The interface to reference bindings declared in wrangler.jsonc
    * @param {ExecutionContext} ctx - The execution context of the Worker
    * @returns {Promise<Response>} The response to be sent back to the client
    """
    async def fetch(self, request):
        # Create a stub to open a communication channel with the Durable Object
        # instance named "foo".
        #
        # Requests from all Workers to the Durable Object instance named "foo"
        # will go to a single remote Durable Object instance.

        # Call the `say_hello()` RPC method on the stub to invoke the method on
        # the remote Durable Object instance.

        url = urlparse(request.url)

        path_parts = (
            url.path.strip("/").split("/")
        )

        # -------------------------------------------
        # API HEALTH
        # -------------------------------------------

        if (
            request.method == "GET"
            and url.path == "/v1/health"
        ):
            return Response.json({
                "ok": True,
                "service": "malcarne-internal-api",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        # -------------------------------------------
        # ROUND ROBIN
        # -------------------------------------------

        if (
            request.method == "POST"
            and len(path_parts) == 5
            and path_parts[0] == "v1"
            and path_parts[1] == "public"
            and path_parts[2] == "round-robin"
            and path_parts[3] == "phone"
        ):
            pool_name = (path_parts[4].lower())

            pool = PHONE_POOLS.get(pool_name)

            if pool is None:
                return Response.json({
                    "ok": False,
                    "error": f"Pool '{pool_name}' not found."
                }, status=404)

            stub = (
                self.env.ROUND_ROBIN.getByName(pool_name)
            )

            index = await stub.next_index(len(pool))

            return Response.json({
                "pool": pool_name,
                "phone": pool[index],
                "pool_size": len(pool)
            })

        # -------------------------------------------
        # Site Health
        # -------------------------------------------
        if (
            request.method == "GET"
            and len(path_parts) == 4
            and path_parts[0] == "v1"
            and path_parts[1] == "public"
            and path_parts[2] == "status"
        ):
            if path_parts[3] == "malcarne":
                site_response_mal = await fetch(
                    "https://malcarne.com/",
                    method="HEAD"
                )

                site_response_malCorp = await fetch(
                    "https://malcarnecorporation.com/",
                    method="HEAD"
                )

                return Response.json({
                    "malcarne": {
                        "status": site_response_mal.status,
                        "ok": site_response_mal.ok
                    },
                    "malcarnecorporation": {
                        "status": site_response_malCorp.status,
                        "ok": site_response_malCorp.ok
                    }
                })
                

        # -------------------------------------------
        # 404
        # -------------------------------------------

        return Response.json({
            "ok": False,
            "error": "Endpoint not found."
        }, status=404)


