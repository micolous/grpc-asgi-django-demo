-- If the original `:status` from the gRPC server was HTTP 200 OK, set the HTTP
-- status code to the content of the `x-http-code` response header (if present).
--
-- This allows a gRPC server to send arbitrary HTTP status codes through the
-- gRPC-JSON transcoder. This is useful when using the transcoder to send
-- arbitrary HTTP responses from a gRPC server (ie: HTTP-over-gRPC).
--
-- This *does not* execute when a gRPC server sends an error response:
-- `convert_grpc_status: true` tells Envoy to convert the `google.rpc.Status`
-- message into JSON, and choose an appropriate error code based on the
-- `StatusCode`.
--
-- https://github.com/envoyproxy/envoy/issues/21839#issuecomment-1164916248

-- Return `true` if the string `s` is empty or `nil`.
local function isempty(s)
    return s == nil or s == ''
end

function envoy_on_response(response_handle)
    local headers = response_handle:headers()
    local custom_response_code = headers:get("x-http-code")
    if headers:get(":status") == "200" and (not isempty(custom_response_code)) then
        headers:replace(":status", custom_response_code)
    end
end
