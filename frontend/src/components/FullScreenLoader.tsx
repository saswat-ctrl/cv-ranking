export default function FullScreenLoader() {
    return (
        <div style={{
            position: 'fixed',
            inset: 0,
            zIndex: 9999,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'white'
        }}>
            <div style={{
                height: '64px',
                width: '64px',
                borderRadius: '50%',
                border: '4px solid #e5e7eb',
                borderTopColor: '#16a34a', // green-600
                animation: 'spin 1s linear infinite'
            }}></div>
            <style jsx>{`
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
}
