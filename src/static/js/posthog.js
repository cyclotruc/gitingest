/* eslint-disable */
!function (t, e) {
    let o, n, p, r;
    if (e.__SV) {return;}                 // already loaded

    window.posthog = e;
    e._i = [];
    e.init = function (i, s, a) {
        function g(t, e) {
            const o = e.split(".");
            if (o.length === 2) {
                t = t[o[0]];
                e = o[1];
            }
            t[e] = function () {
                t.push([e].concat(Array.prototype.slice.call(arguments, 0)));
            };
        }

        p = t.createElement("script");
        p.type = "text/javascript";
        p.crossOrigin = "anonymous";
        p.async = true;
        p.src = `${ s.api_host.replace(".i.posthog.com", "-assets.i.posthog.com") }/static/array.js`;

        r = t.getElementsByTagName("script")[0];
        r.parentNode.insertBefore(p, r);

        let u = e;
        if (a !== undefined) {
            u = e[a] = [];
        } else {
            a = "posthog";
        }

        u.people = u.people || [];
        u.toString = function (t) {
            let e = "posthog";
            if (a !== "posthog") {e += `.${ a }`;}
            if (!t) {e += " (stub)";}
            return e;
        };
        u.people.toString = function () {
            return `${ u.toString(1) }.people (stub)`;
        };


        o = [
            "init", "capture", "register", "register_once", "register_for_session", "unregister",
            "unregister_for_session", "getFeatureFlag", "getFeatureFlagPayload", "isFeatureEnabled",
            "reloadFeatureFlags", "updateEarlyAccessFeatureEnrollment", "getEarlyAccessFeatures",
            "on", "onFeatureFlags", "onSessionId", "getSurveys", "getActiveMatchingSurveys",
            "renderSurvey", "canRenderSurvey", "getNextSurveyStep", "identify", "setPersonProperties",
            "group", "resetGroups", "setPersonPropertiesForFlags", "resetPersonPropertiesForFlags",
            "setGroupPropertiesForFlags", "resetGroupPropertiesForFlags", "reset", "get_distinct_id",
            "getGroups", "get_session_id", "get_session_replay_url", "alias", "set_config",
            "startSessionRecording", "stopSessionRecording", "sessionRecordingStarted",
            "captureException", "loadToolbar", "get_property", "getSessionProperty",
            "createPersonProfile", "opt_in_capturing", "opt_out_capturing",
            "has_opted_in_capturing", "has_opted_out_capturing", "clear_opt_in_out_capturing",
            "debug", "getPageViewId"
        ];

        for (n = 0; n < o.length; n++) {g(u, o[n]);}
        e._i.push([i, s, a]);
    };

    e.__SV = 1;
}(document, window.posthog || []);

/* Initialise PostHog */
posthog.init('phc_9aNpiIVH2zfTWeY84vdTWxvrJRCQQhP5kcVDXUvcdou', {
    api_host: 'https://eu.i.posthog.com',
    person_profiles: 'always',
});
