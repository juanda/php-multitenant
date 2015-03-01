# output as png image
set terminal png size 600
 
# save file to "out.png"
set output "results.png"
 
# graph title
set title "1000 peticiones, 20 peticiones concurrentes"
 
# nicer aspect ratio for image size
set size ratio 0.6
 
# y-axis grid
set grid y
 
# x-axis label
set xlabel "peticiones"
 
# y-axis label
set ylabel "tiempo de respuesta (ms)"
 
# plot data from "out.dat" using column 9 with smooth sbezier lines
# and title of "nodejs" for the given data
plot "result.tsv" using 9 smooth sbezier with lines title "nuestra-app.com"
