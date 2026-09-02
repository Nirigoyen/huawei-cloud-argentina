const { useState, useEffect, useRef } = require('react');

function useFetch(url) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const isMounted = useRef(true);

    useEffect(() => {
        isMounted.current = true;
        setLoading(true);
        setError(null);
        setData(null);

        fetch(url)
            .then((res) => {
                if (!res.ok) {
                    throw new Error(`HTTP error: ${res.status}`);
                }
                return res.json();
            })
            .then((data) => {
                if (isMounted.current) {
                    setData(data);
                    setLoading(false);
                }
            })
            .catch((err) => {
                if (isMounted.current) {
                    setError(err);
                    setLoading(false);
                }
            });

        return () => {
            isMounted.current = false;
        };
    }, [url]);

    return { data, loading, error };
}

module.exports = { useFetch };
