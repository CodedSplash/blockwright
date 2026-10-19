program Lab;
{ Лабораторная: максимум и сортировка }
const N = 10;
var
  a: array[1..N] of integer;
  i, j, t, max: integer;

function IsEven(x: integer): boolean;
begin
  IsEven := x mod 2 = 0;
end;

procedure Swap(var x, y: integer);
var tmp: integer;
begin
  tmp := x; x := y; y := tmp;
end;

procedure Fill;
var k: integer;
begin
  for k := 1 to N do
  begin
    write('a[', k, '] = ');
    readln(a[k]);
  end;
end;

begin
  Fill;
  max := a[1];
  for i := 2 to N do
    if a[i] > max then
      max := a[i];
  writeln('Максимум: ', max);
  for i := N downto 2 do
    for j := 1 to i - 1 do
      if a[j] > a[j + 1] then
        Swap(a[j], a[j + 1]);
  i := 0;
  repeat
    i := i + 1;
    if IsEven(a[i]) then continue;
    write(a[i], ' ');
  until i >= N;
  writeln;
  case max mod 3 of
    0: writeln('делится на 3');
    1, 2:
      begin
        writeln('остаток ', max mod 3);
        exit;
      end;
  else
    writeln('?');
  end;
  while True do
  begin
    t := t + 1;
    if t > 100 then break;
  end;
  try
    t := 100 div max;
  except
    on E: EDivByZero do writeln('деление на ноль');
  end;
  readln;
end.
