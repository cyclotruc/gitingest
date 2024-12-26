// Snow effect initialization
function initSnow() {
    const snowCanvas = document.getElementById('snow-canvas');
    const ctx = snowCanvas.getContext('2d');

    // Configure snow
    const snowflakes = [];
    const maxSnowflakes = 50;
    const spawnInterval = 200;
    let currentSnowflakes = 0;
    let lastSpawnTime = 0;

    // Resize canvas to window size
    function resizeCanvas() {
        snowCanvas.width = window.innerWidth;
        snowCanvas.height = window.innerHeight;
    }

    // Initial setup
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Snowflake class definition
    class Snowflake {
        constructor() {
            this.reset();
        }

        reset() {
            this.x = Math.random() * snowCanvas.width;
            this.y = 0;
            this.size = Math.random() * 3 + 2;
            this.speed = Math.random() * 1 + 0.5;
            this.wind = Math.random() * 0.5 - 0.25;
        }

        update() {
            this.y += this.speed;
            this.x += this.wind;

            if (this.y > snowCanvas.height) {
                this.reset();
            }
        }

        draw() {
            ctx.save();

            ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
            ctx.shadowBlur = 5;
            ctx.shadowOffsetX = 2;
            ctx.shadowOffsetY = 2;

            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(255, 255, 255, 1)';
            ctx.fill();

            ctx.strokeStyle = 'rgba(200, 200, 200, 0.8)';
            ctx.lineWidth = 0.5;
            ctx.stroke();

            ctx.restore();
        }
    }

    function animate(currentTime) {
        ctx.clearRect(0, 0, snowCanvas.width, snowCanvas.height);

        if (currentSnowflakes < maxSnowflakes && currentTime - lastSpawnTime > spawnInterval) {
            snowflakes.push(new Snowflake());
            currentSnowflakes++;
            lastSpawnTime = currentTime;
        }

        snowflakes.forEach(snowflake => {
            snowflake.update();
            snowflake.draw();
        });

        requestAnimationFrame(animate);
    }

    requestAnimationFrame(animate);
}

// Initialize snow when DOM content is loaded
document.addEventListener('DOMContentLoaded', initSnow);

// Also initialize when the HTMX content is swapped
document.addEventListener('htmx:afterSettle', initSnow);
