import express, { Express, Request, Response } from "express";
import { engine } from "express-handlebars";
import * as openid_client from "openid-client";
import { jwtDecode, JwtPayload } from "jwt-decode";
import cookieParser from "cookie-parser";
import { DoubleCsrfCookieOptions, doubleCsrf } from "csrf-csrf";
import jwt, { JsonWebTokenError } from "jsonwebtoken";
import jwkToPem from "jwk-to-pem";
import bodyParser from "body-parser";
import { handlebarsHelpers } from "./pkg";
import { logger, middleware as middlewareLogger } from "./pkg/logger";
import {
  registerConsentRoute,
  registerErrorRoute,
  registerLoginRoute,
  registerStaticRoutes,
} from "./routes";
import { csrfErrorHandler } from "./routes/csrfError";
import { fileURLToPath } from "url";
import { dirname } from "path";

// import session, {MemoryStore} from 'express-session';
// import {createClient} from 'redis';
// import { RedisStore } from 'connect-redis';

// const REDIS_CLIENT = createClient()
// REDIS_CLIENT.connect().catch(console.error)
// const redis_store = new RedisStore({
//   client: REDIS_CLIENT,
//   prefix: 'fairplex-client:'
// })

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export interface CustomSessionData {
  code_verifier?: string;
  id_token?: string;
  access_token?: string;
  state?: string;
  // payload?: any;
  accessTokenDecoded?: JwtPayload;
  idTokenDecoded?: JwtPayload;
  passportToken?: string;
  passportTokenDecoded?: JwtPayload;
  // pemId?: string;
  // pemAccess?: string;
  idTokenVerified?: boolean;
  accessTokenVerified?: boolean;
  passportTokenVerified?: boolean;
  destinationAmpPdGCSUrl?: string;
  sourceAmpPdDRSUrl?: string;
  ampPdDataTransferredTo?: string;
  ampPdDataTransferredMessage?: string;
}

const cookieOptions: DoubleCsrfCookieOptions = {
  sameSite: "lax",
  signed: true,
  // set secure cookies by default (recommended in production)
  // can be disabled through DANGEROUSLY_DISABLE_SECURE_COOKIES=true env var
  secure: true,
  ...(process.env.DANGEROUSLY_DISABLE_SECURE_CSRF_COOKIES && {
    secure: false,
  }),
};

const cookieName = process.env.CSRF_COOKIE_NAME || "__Host-ax-x-csrf-token";
const cookieSecret = process.env.CSRF_COOKIE_SECRET;

// Sets up csrf protection
const {
  invalidCsrfTokenError,
  generateToken,
  validateRequest,
  doubleCsrfProtection, // This is the default CSRF protection middleware.
} = doubleCsrf({
  getSecret: () => cookieSecret || "", // A function that optionally takes the request and returns a secret
  cookieName: cookieName, // The name of the cookie to be used, recommend using Host prefix.
  cookieOptions,
  ignoredMethods: ["GET", "HEAD", "OPTIONS", "PUT", "DELETE"], // A list of request methods that will not be protected.
  getTokenFromRequest: (req: Request) => {
    logger.debug("Getting CSRF token from request", { body: req.body });
    return req.body._csrf;
  }, // A function that returns the token from the request
});

const app: Express = express();
const router = express.Router();
const port = process.env.MY_PORT;
app.use(cookieParser(process.env.COOKIE_SECRET || ""));
app.use(bodyParser.urlencoded({ extended: false }));
app.use(middlewareLogger);
app.set("view engine", "hbs");
app.engine(
  "hbs",
  engine({
    extname: "hbs",
    layoutsDir: `${__dirname}/../views/layouts/`,
    partialsDir: `${__dirname}/../views/partials/`,
    defaultLayout: "auth",
    helpers: handlebarsHelpers,
  })
);

const customSession = new Map<string, CustomSessionData>();

registerLoginRoute(router);
registerErrorRoute(router);
// all routes registered under the /consent path are protected by CSRF
router.use("/consent", doubleCsrfProtection);
router.use("/consent", csrfErrorHandler(invalidCsrfTokenError));
registerConsentRoute(router);
registerStaticRoutes(router);

let server: URL = new URL(
  `${
    process.env.HYDRA_PRIVATE_URL || process.env.HYDRA_URL
  }/.well-known/openid-configuration`
); // Authorization Server's Issuer Identifier
let clientId: string = process.env.HYDRA_CLIENT_ID!; // Client identifier at the Authorization Server
let clientSecret: string = process.env.HYDRA_CLIENT_SECRET!; // Client Secret

let config: openid_client.Configuration;

// Initialize OpenID configuration at startup
async function initializeOpenIDConfig() {
  try {
    console.log(
      `Initializing OpenID configuration with server: ${server.toString()}`
    );
    config = await openid_client.discovery(
      server,
      clientId,
      clientSecret,
      undefined,
      {
        execute: [openid_client.allowInsecureRequests],
      }
    );
    console.log("OpenID configuration initialized successfully");
  } catch (error) {
    console.error("Failed to initialize OpenID configuration:", error);
    throw error;
  }
}

// Serve the login page
router.get("/", async (req: Request, res: Response) => {
  let this_session: CustomSessionData | undefined;
  if (req.cookies.sessionID) {
    this_session = customSession.get(req.cookies.sessionID);
    console.log(`got session for id ${req.cookies.sessionID}`);
  } else {
    console.log(`home No session for id ${req.cookies.sessionID}`);
  }
  const idToken = this_session?.id_token || "Not authenticated";
  const decodedIdToken = this_session?.idTokenDecoded || "Not authenticated";
  const accessToken = this_session?.access_token || "Not authenticated";
  const decodedAccessToken =
    this_session?.accessTokenDecoded || "Not authenticated";
  const passportToken = this_session?.passportToken || "Not authenticated";
  const decodedPassportToken =
    this_session?.passportTokenDecoded || "Not authenticated";
  const html = `
    <!DOCTYPE html>
    <html>
      <head>
        <title>FAIRplex GA4GH Federated Authentication Pilot</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; }
          .token-display { 
            word-break: break-all; 
            margin-top: 20px;
            padding: 10px;
            background-color: #f0f0f0;
          }
          .label1 {
            display: block;
            width: 30ch;
            background-color: light-gray;
          }
        </style>
        <base href="/">
      </head>
      <body>
        <h1>FAIRplex GA4GH Federated Authentication Pilot</h1>
        <button onclick="window.location.href='/login-start-flow'">Login</button>
        ${
          this_session
            ? `<div class="token-display">
                <h3>OpenID Token:</h3>
                <p>${idToken}</p>
               </div>
               <div class="token-display">
                <h3>OpenID Token Payload:</h3>
                <pre>${JSON.stringify(decodedIdToken, null, 2)}</pre>
                <bold>Signature verified: ${
                  this_session?.idTokenVerified
                }</bold>
              </div>
          <div class="token-display">
                <h3>OAuth2 Access Token:</h3>
                <p>${accessToken}</p>
               </div>
               <div class="token-display">
                <h3>OAuth2 Access Token Payload:</h3>
                <pre>${JSON.stringify(decodedAccessToken, null, 2)}</pre>
                <bold>Signature verified: ${
                  this_session?.accessTokenVerified
                }</bold>
              </div>
          <div class="token-display">
                <h3>GA4GH Passport Token:</h3>
                <p>${passportToken}</p>
               </div>
               <div class="token-display">
                <h3>GA4GH Passport Payload:</h3>
                <pre>${JSON.stringify(decodedPassportToken, null, 2)}</pre>
                <bold>Signature verified: ${
                  this_session?.passportTokenVerified
                }</bold>
              </div>
          <br>
          <hr>
          <h3>AMP PD Data Transfer</h3>
          <form action="/transfer-amp-pd-data" method="POST">
          <label for="amp-pd-data-source" class="label1">Source DRS URI</label>
            <input type="text" id="amp-pd-data-source" name="amp-pd-data-source" size="100" 
              value=${this_session?.sourceAmpPdDRSUrl}><br><br>
          <label for="amp-pd-data-destination" class="label1">Destination Bucket</label>
            <input type="text" id="amp-pd-data-destination" name="amp-pd-data-destination" size="100" 
              value=${this_session?.destinationAmpPdGCSUrl}><br><br>
            <input type="submit" value="Transfer AMP PD Data">
          </form>
              `
            : ""
        }
        ${
          this_session?.ampPdDataTransferredMessage
            ? `<div class="token-display">
                <h4>AMP PD Data Transferred To:</h4>
                <p>${this_session?.ampPdDataTransferredTo}</p>
                <h4>Message:</h4>
                <p>${this_session?.ampPdDataTransferredMessage}</p>
            </div>`
            : ""
        }

      </body>
    </html>
  `;
  res.send(html);
});

function parseGCSUri(uri: string) {
  if (!uri.startsWith("gs://")) {
    throw new Error('Invalid GCS URI: Must start with "gs://"');
  }

  const parts = uri.substring(5).split("/");
  const bucket = parts[0];
  const path = parts.slice(1).join("/");

  return { bucket, path };
}

// A separate search/discovery mechanism will provide the actual DRS URI for the requested data object
const AMP_PD_DRS_URI: string = process.env.AMP_PD_DRS_URI!;
const AMP_PD_DESTINATION_URI: string = process.env.AMP_PD_DESTINATION_URI!;

router.post(
  "/transfer-amp-pd-data",
  async (req: express.Request, res: express.Response) => {
    console.log(`getting AMP PD data:${JSON.stringify(req.body)}`);
    const this_session = customSession.get(req.cookies.sessionID);
    if (!this_session) {
      console.error(
        `Did not find session in transfer for id ${req.cookies.sessionID}`
      );
      return;
    }
    this_session.sourceAmpPdDRSUrl = req.body["amp-pd-data-source"];
    this_session.destinationAmpPdGCSUrl = req.body["amp-pd-data-destination"];
    const { bucket: dest_bucket, path: dest_path } = parseGCSUri(
      this_session.destinationAmpPdGCSUrl!
    );
    const response = await fetch(this_session.sourceAmpPdDRSUrl!, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ passports: [this_session.passportToken] }),
    });
    const data = await response.json();
    console.log(data);
    const AUTH_PILOT_DATA_TRANSFER_URL: string =
      process.env.AUTH_PILOT_DATA_TRANSFER_URL!;
    const downloadresponse = await fetch(AUTH_PILOT_DATA_TRANSFER_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        signed_url: data["signed_url"],
        destination_bucket: dest_bucket,
        destination_path: dest_path,
      }),
    });

    const dataTransferResult = await downloadresponse.json();
    console.log(dataTransferResult);
    this_session.ampPdDataTransferredTo = dataTransferResult["gcs_url"];
    this_session.ampPdDataTransferredMessage = dataTransferResult["message"];

    res.redirect("/");
  }
);

// Handle login initiation
router.get("/login-start-flow", async (req: Request, res: Response) => {
  // Config is now initialized at startup
  if (config === undefined) {
    console.error("OpenID configuration not initialized");
    res.status(500).send("Server configuration error");
    return;
  }
  /**
   * Value used in the authorization request as the redirect_uri parameter, this
   * is typically pre-registered at the Authorization Server.
   */
  let redirect_uri: string = process.env.OAUTH_CALLBACK!; // Redirect URI
  let scope: string = "openid profile email ga4gh_passport_v1"; // Scope of the access request
  /**
   * PKCE: The following MUST be generated for every redirect to the
   * authorization_endpoint. You must store the code_verifier and state in the
   * end-user session such that it can be recovered as the user gets redirected
   * from the authorization server back to your application.
   */
  let code_verifier: string = openid_client.randomPKCECodeVerifier();
  let code_challenge: string = await openid_client.calculatePKCECodeChallenge(
    code_verifier
  );
  let state: string = openid_client.randomState();
  // Store the code_verifier in session for later use
  res.cookie("sessionID", state, {
    httpOnly: true,
    secure: true, // Use true in production. Requires HTTPS
    sameSite: "lax",
    maxAge: 3600000, // 1 hour in milliseconds
    path: "/",
  });
  customSession.set(state, {
    state: state,
    code_verifier: code_verifier,
  } as CustomSessionData);

  let parameters: Record<string, string> = {
    redirect_uri,
    scope,
    code_challenge,
    code_challenge_method: "S256",
    state,
  };

  // if (!config.serverMetadata().supportsPKCE()) {
  //   /**
  //    * We cannot be sure the server supports PKCE so we're going to use state too.
  //    * Use of PKCE is backwards compatible even if the AS doesn't support it which
  //    * is why we're using it regardless. Like PKCE, random state must be generated
  //    * for every redirect to the authorization_endpoint.
  //    */
  //   parameters.state = state
  // }

  let redirectTo: URL = openid_client.buildAuthorizationUrl(config, parameters);

  // now redirect the user to redirectTo.href (Hydra)
  console.log(
    "fairplex-client/login-start-flow redirecting to",
    redirectTo.href
  );

  res.redirect(redirectTo.href);
});

// Handle the callback from the OIDC provider
router.get("/callback", async (req: Request, res: Response) => {
  try {
    const this_session = customSession.get(req.cookies.sessionID);
    if (!this_session) {
      console.error(
        `callback Did not find session for ${req.cookies.sessionID}`
      );
      return;
    }

    // const currentUrl = new URL(`${req.protocol}://${req.get('host')}${req.originalUrl}`);
    const currentUrl = new URL(`${process.env.MY_HOST}${req.originalUrl}`);
    console.log(`oauth callback currentUrl=${currentUrl}`);
    let tokens: openid_client.TokenEndpointResponse =
      await openid_client.authorizationCodeGrant(
        config,
        currentUrl,
        {
          pkceCodeVerifier: this_session.code_verifier,
          expectedState: this_session.state,
        },
        {
          tokenEndpointAuthMethod: "client_secret_post",
        }
      );

    console.log("Token Endpoint Response", tokens);
    this_session.id_token = tokens.id_token!;
    const decodedIdToken = jwtDecode(tokens.id_token!);
    this_session.idTokenDecoded = decodedIdToken;
    console.log("Decoded Id Token", decodedIdToken);
    this_session.access_token = tokens.access_token;
    const decodedAccessToken = jwtDecode(tokens.access_token);
    this_session.accessTokenDecoded = decodedAccessToken;
    console.log("Decoded Access Token", decodedAccessToken);

    // Get public key from JWKS endpoint
    const jwks_uri = config.serverMetadata().jwks_uri;
    console.log(jwks_uri);
    if (!jwks_uri) {
      throw new Error("Missing jwks_uri in server metadata");
    }
    let jwksResponse = await fetch(jwks_uri, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    });
    const jwksData = await jwksResponse.json();
    console.log(JSON.stringify(jwksData["keys"]));

    // Verify the id token using the public key
    for (const jwk of jwksData["keys"]) {
      try {
        const pem_id = jwkToPem(jwk);
        // req.session?.pemId = pem_id;
        const verifiedIdToken = jwt.verify(tokens.id_token!, pem_id, {
          algorithms: ["RS256"],
        });
        this_session.idTokenVerified = verifiedIdToken !== undefined;
        if (this_session.idTokenVerified) {
          console.log("Verified Id Token", verifiedIdToken);
          break;
        }
      } catch (error) {
        console.error("ERROR while verifying ID token:" + error);
      }
    }

    // Verify the access token using the public key
    for (const jwk of jwksData["keys"]) {
      try {
        const pemAccess = jwkToPem(jwk);
        // req.session?.pemAccess = pemAccess;
        const verifiedAccessToken = jwt.verify(tokens.access_token, pemAccess, {
          algorithms: ["RS256"],
        });
        this_session.accessTokenVerified = verifiedAccessToken !== undefined;
        if (this_session.accessTokenVerified) {
          console.log("Verified Access Token", verifiedAccessToken);
          break;
        }
      } catch (error) {
        console.error("ERROR while verifying access token:" + error);
      }
    }

    this_session.idTokenDecoded = decodedIdToken;

    // Token exchange for passport
    const tokenExchangeUrl = process.env.AUTH_PILOT_TOKEN_EXCHANGE_URL!;
    const response = await fetch(tokenExchangeUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        grant_type: "urn:ietf:params:oauth:grant-type:token-exchange",
        subject_token: tokens.access_token,
        requested_token_type: "urn:ga4gh:params:oauth:token-type:passport",
        subject_token_type: "urn:ietf:params:oauth:token-type:access_token",
        resource: AMP_PD_DRS_URI,
      }).toString(),
    });

    const passportResult = await response.json();
    console.log("Passport Token exchange result", passportResult);

    this_session.passportToken = passportResult.access_token;
    this_session.passportTokenDecoded = jwtDecode(passportResult.access_token);
    console.log("Decoded Passport Token", this_session.passportTokenDecoded);

    // Verify the passport token using the public key
    for (const jwk of jwksData["keys"]) {
      try {
        const pemAccess = jwkToPem(jwk);
        const verifiedPassport = jwt.verify(
          passportResult.access_token,
          pemAccess,
          { algorithms: ["RS256"] }
        );
        this_session.passportTokenVerified = verifiedPassport !== undefined;
        console.log("Verified Passport Token", verifiedPassport);
      } catch (error) {}
    }

    this_session.sourceAmpPdDRSUrl = AMP_PD_DRS_URI;
    this_session.destinationAmpPdGCSUrl = AMP_PD_DESTINATION_URI;

    // // Redirect back to the home page
    res.redirect("/");
  } catch (error) {
    console.error("Error during authentication:", error);
    res.status(500).send("Authentication failed");
  }
});

app.use("/", router);

// Initialize and start the server
async function startServer() {
  try {
    await initializeOpenIDConfig();
    const portNumber = parseInt(port || "8884", 10);
    app.listen(portNumber, "0.0.0.0", () => {
      console.log(`App listening at port ${portNumber} on all interfaces`);
    });
  } catch (error) {
    console.error("Failed to start server:", error);
    process.exit(1);
  }
}

startServer();
